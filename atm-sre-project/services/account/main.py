import json
import os

import psycopg2
import redis
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/bankdb")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"

BALANCE_TTL = 30       # seconds
ACCOUNT_INFO_TTL = 300  # 5 minutes

app = FastAPI(title="Account Service")
Instrumentator().instrument(app).expose(app)

bearer_scheme = HTTPBearer()
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    jti = payload.get("jti")
    if jti and redis_client.exists(f"blacklist:{jti}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    return payload


class AccountOut(BaseModel):
    id: int
    account_number: str
    owner_name: str
    currency: str
    balance: float


class BalanceOut(BaseModel):
    account_number: str
    balance: float


@app.get("/health")
def health():
    return {"status": "ok", "service": "account"}


@app.get("/account/{account_number}", response_model=AccountOut)
def get_account(account_number: str, auth=Depends(require_auth), db=Depends(get_db)):
    cache_key = f"account_info:{account_number}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    cur = db.cursor()
    cur.execute(
        """
        SELECT a.id, a.account_number, u.name, a.currency, a.balance
        FROM accounts a
        JOIN users u ON u.id = a.user_id
        WHERE a.account_number = %s
        """,
        (account_number,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")

    result = AccountOut(
        id=row[0],
        account_number=row[1],
        owner_name=row[2],
        currency=row[3],
        balance=float(row[4]),
    )
    redis_client.setex(cache_key, ACCOUNT_INFO_TTL, result.model_dump_json())
    return result


@app.get("/account/{account_number}/balance", response_model=BalanceOut)
def get_balance(account_number: str, auth=Depends(require_auth), db=Depends(get_db)):
    cache_key = f"balance:{account_number}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    cur = db.cursor()
    cur.execute("SELECT balance FROM accounts WHERE account_number = %s", (account_number,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")

    result = BalanceOut(account_number=account_number, balance=float(row[0]))
    redis_client.setex(cache_key, BALANCE_TTL, result.model_dump_json())
    return result
