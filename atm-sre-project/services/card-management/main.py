import os

import bcrypt
import psycopg2
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

redis_client = redis.from_url(REDIS_URL, decode_responses=True)
bearer_scheme = HTTPBearer()

app = FastAPI(title="Card & Account Management Service")
Instrumentator().instrument(app).expose(app)


# ── Auth ──────────────────────────────────────────────────────────────────────

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


# ── Models ────────────────────────────────────────────────────────────────────

class CardOut(BaseModel):
    id: int
    card_number: str
    account_number: str
    is_blocked: bool
    daily_limit: float


class BlockCardRequest(BaseModel):
    reason: str | None = None


class UnblockCardRequest(BaseModel):
    reason: str | None = None


class ChangePinRequest(BaseModel):
    current_pin: str
    new_pin: str


class UpdateLimitRequest(BaseModel):
    daily_limit: condecimal(gt=0, decimal_places=2)


# ── Helpers ───────────────────────────────────────────────────────────────────

def invalidate_account_cache(account_number: str):
    redis_client.delete(f"balance:{account_number}")
    redis_client.delete(f"account_info:{account_number}")


def get_card_row(cur, card_number: str) -> tuple:
    cur.execute(
        "SELECT id, card_number, account_number, is_blocked, daily_limit FROM cards WHERE card_number = %s",
        (card_number,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Card not found")
    return row


def assert_account_owner(payload: dict, account_number: str):
    """Ensure the JWT owner matches the account being modified."""
    if payload.get("account_number") != account_number:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "card-management"}


@app.get("/card/{card_number}", response_model=CardOut)
def get_card(card_number: str, auth=Depends(require_auth), db=Depends(get_db)):
    cur = db.cursor()
    row = get_card_row(cur, card_number)
    assert_account_owner(auth, row[2])
    return CardOut(id=row[0], card_number=row[1], account_number=row[2],
                   is_blocked=row[3], daily_limit=float(row[4]))


@app.post("/card/{card_number}/block", response_model=CardOut)
def block_card(card_number: str, body: BlockCardRequest, auth=Depends(require_auth), db=Depends(get_db)):
    cur = db.cursor()
    row = get_card_row(cur, card_number)
    assert_account_owner(auth, row[2])

    if row[3]:
        raise HTTPException(status_code=422, detail="Card is already blocked")

    cur.execute("UPDATE cards SET is_blocked = TRUE WHERE card_number = %s", (card_number,))
    db.commit()
    return CardOut(id=row[0], card_number=row[1], account_number=row[2],
                   is_blocked=True, daily_limit=float(row[4]))


@app.post("/card/{card_number}/unblock", response_model=CardOut)
def unblock_card(card_number: str, body: UnblockCardRequest, auth=Depends(require_auth), db=Depends(get_db)):
    cur = db.cursor()
    row = get_card_row(cur, card_number)
    assert_account_owner(auth, row[2])

    if not row[3]:
        raise HTTPException(status_code=422, detail="Card is not blocked")

    cur.execute("UPDATE cards SET is_blocked = FALSE WHERE card_number = %s", (card_number,))
    db.commit()
    return CardOut(id=row[0], card_number=row[1], account_number=row[2],
                   is_blocked=False, daily_limit=float(row[4]))


@app.put("/card/{card_number}/limit", response_model=CardOut)
def update_limit(card_number: str, body: UpdateLimitRequest, auth=Depends(require_auth), db=Depends(get_db)):
    cur = db.cursor()
    row = get_card_row(cur, card_number)
    assert_account_owner(auth, row[2])

    new_limit = float(body.daily_limit)
    cur.execute("UPDATE cards SET daily_limit = %s WHERE card_number = %s", (new_limit, card_number))
    db.commit()
    return CardOut(id=row[0], card_number=row[1], account_number=row[2],
                   is_blocked=row[3], daily_limit=new_limit)


@app.post("/card/change-pin")
def change_pin(body: ChangePinRequest, auth=Depends(require_auth), db=Depends(get_db)):
    account_number = auth.get("account_number")
    cur = db.cursor()

    cur.execute("SELECT id, pin_hash FROM users WHERE account_number = %s", (account_number,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    if not bcrypt.checkpw(body.current_pin.encode(), row[1].encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current PIN is incorrect")

    new_hash = bcrypt.hashpw(body.new_pin.encode(), bcrypt.gensalt(12)).decode()
    cur.execute("UPDATE users SET pin_hash = %s WHERE id = %s", (new_hash, row[0]))
    db.commit()

    # Invalidate any cached account data
    invalidate_account_cache(account_number)
    return {"detail": "PIN changed successfully"}


@app.get("/card/account/{account_number}/cards")
def list_cards(account_number: str, auth=Depends(require_auth), db=Depends(get_db)):
    assert_account_owner(auth, account_number)
    cur = db.cursor()
    cur.execute(
        "SELECT id, card_number, account_number, is_blocked, daily_limit FROM cards WHERE account_number = %s",
        (account_number,),
    )
    rows = cur.fetchall()
    return [
        CardOut(id=r[0], card_number=r[1], account_number=r[2],
                is_blocked=r[3], daily_limit=float(r[4]))
        for r in rows
    ]
