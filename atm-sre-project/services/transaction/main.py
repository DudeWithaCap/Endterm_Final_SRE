import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
import psycopg2
import psycopg2.extras
import redis
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, condecimal

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/bankdb")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
HISTORY_URL = os.getenv("HISTORY_SERVICE_URL", "http://history:8004")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)
bearer_scheme = HTTPBearer()

_http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _http_client
    _http_client = httpx.AsyncClient(timeout=5.0)
    yield
    await _http_client.aclose()


app = FastAPI(title="Transaction Service", lifespan=lifespan)
Instrumentator().instrument(app).expose(app)


# ── Auth helpers ──────────────────────────────────────────────────────────────

def require_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    jti = payload.get("jti")
    if jti and redis_client.exists(f"blacklist:{jti}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    return payload


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


# ── History event emitter ─────────────────────────────────────────────────────

async def emit_history_event(event: dict):
    """Fire-and-forget: send transaction event to History Service."""
    try:
        await _http_client.post(f"{HISTORY_URL}/history/events", json=event)
    except Exception:
        # History Service may not exist yet (Phase 3); log and continue
        pass


# ── Request / Response models ─────────────────────────────────────────────────

class DepositRequest(BaseModel):
    account_number: str
    amount: condecimal(gt=0, decimal_places=2)


class WithdrawRequest(BaseModel):
    account_number: str
    amount: condecimal(gt=0, decimal_places=2)


class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: condecimal(gt=0, decimal_places=2)


class TransactionOut(BaseModel):
    id: int
    type: str
    from_account: str | None
    to_account: str | None
    amount: float
    status: str
    created_at: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def invalidate_balance_cache(account_number: str):
    redis_client.delete(f"balance:{account_number}")
    redis_client.delete(f"account_info:{account_number}")


def record_transaction(cur, tx_type: str, from_acct: str | None, to_acct: str | None, amount: float, tx_status: str = "success") -> int:
    cur.execute(
        """
        INSERT INTO transactions (from_account, to_account, amount, type, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, created_at
        """,
        (from_acct, to_acct, amount, tx_type, tx_status),
    )
    row = cur.fetchone()
    return row[0], row[1]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "transaction"}


@app.post("/transaction/deposit", response_model=TransactionOut)
async def deposit(body: DepositRequest, auth=Depends(require_auth), db=Depends(get_db)):
    amount = float(body.amount)
    cur = db.cursor()

    cur.execute("SELECT id FROM accounts WHERE account_number = %s FOR UPDATE", (body.account_number,))
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Account not found")

    cur.execute(
        "UPDATE accounts SET balance = balance + %s WHERE account_number = %s",
        (amount, body.account_number),
    )
    tx_id, created_at = record_transaction(cur, "deposit", None, body.account_number, amount)
    db.commit()

    invalidate_balance_cache(body.account_number)

    event = {
        "transaction_id": tx_id,
        "type": "deposit",
        "to_account": body.account_number,
        "amount": amount,
        "status": "success",
        "created_at": created_at.isoformat(),
    }
    await emit_history_event(event)

    return TransactionOut(
        id=tx_id, type="deposit", from_account=None,
        to_account=body.account_number, amount=amount, status="success",
        created_at=created_at.isoformat(),
    )


@app.post("/transaction/withdraw", response_model=TransactionOut)
async def withdraw(body: WithdrawRequest, auth=Depends(require_auth), db=Depends(get_db)):
    amount = float(body.amount)
    cur = db.cursor()

    cur.execute("SELECT balance FROM accounts WHERE account_number = %s FOR UPDATE", (body.account_number,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")

    if float(row[0]) < amount:
        tx_id, created_at = record_transaction(cur, "withdraw", body.account_number, None, amount, "failed")
        db.commit()
        event = {
            "transaction_id": tx_id, "type": "withdraw",
            "from_account": body.account_number, "amount": amount,
            "status": "failed", "created_at": created_at.isoformat(),
        }
        await emit_history_event(event)
        raise HTTPException(status_code=422, detail="Insufficient funds")

    cur.execute(
        "UPDATE accounts SET balance = balance - %s WHERE account_number = %s",
        (amount, body.account_number),
    )
    tx_id, created_at = record_transaction(cur, "withdraw", body.account_number, None, amount)
    db.commit()

    invalidate_balance_cache(body.account_number)

    event = {
        "transaction_id": tx_id, "type": "withdraw",
        "from_account": body.account_number, "amount": amount,
        "status": "success", "created_at": created_at.isoformat(),
    }
    await emit_history_event(event)

    return TransactionOut(
        id=tx_id, type="withdraw", from_account=body.account_number,
        to_account=None, amount=amount, status="success",
        created_at=created_at.isoformat(),
    )


@app.post("/transaction/transfer", response_model=TransactionOut)
async def transfer(body: TransferRequest, auth=Depends(require_auth), db=Depends(get_db)):
    if body.from_account == body.to_account:
        raise HTTPException(status_code=422, detail="Cannot transfer to the same account")

    amount = float(body.amount)
    cur = db.cursor()

    # Lock both rows in consistent order to avoid deadlocks
    ordered = sorted([body.from_account, body.to_account])
    cur.execute(
        "SELECT account_number, balance FROM accounts WHERE account_number = ANY(%s) FOR UPDATE",
        (ordered,),
    )
    rows = {r[0]: float(r[1]) for r in cur.fetchall()}

    if body.from_account not in rows:
        raise HTTPException(status_code=404, detail="Source account not found")
    if body.to_account not in rows:
        raise HTTPException(status_code=404, detail="Destination account not found")

    if rows[body.from_account] < amount:
        tx_id, created_at = record_transaction(
            cur, "transfer", body.from_account, body.to_account, amount, "failed"
        )
        db.commit()
        event = {
            "transaction_id": tx_id, "type": "transfer",
            "from_account": body.from_account, "to_account": body.to_account,
            "amount": amount, "status": "failed", "created_at": created_at.isoformat(),
        }
        await emit_history_event(event)
        raise HTTPException(status_code=422, detail="Insufficient funds")

    cur.execute(
        "UPDATE accounts SET balance = balance - %s WHERE account_number = %s",
        (amount, body.from_account),
    )
    cur.execute(
        "UPDATE accounts SET balance = balance + %s WHERE account_number = %s",
        (amount, body.to_account),
    )
    tx_id, created_at = record_transaction(
        cur, "transfer", body.from_account, body.to_account, amount
    )
    db.commit()

    invalidate_balance_cache(body.from_account)
    invalidate_balance_cache(body.to_account)

    event = {
        "transaction_id": tx_id, "type": "transfer",
        "from_account": body.from_account, "to_account": body.to_account,
        "amount": amount, "status": "success", "created_at": created_at.isoformat(),
    }
    await emit_history_event(event)

    return TransactionOut(
        id=tx_id, type="transfer", from_account=body.from_account,
        to_account=body.to_account, amount=amount, status="success",
        created_at=created_at.isoformat(),
    )
