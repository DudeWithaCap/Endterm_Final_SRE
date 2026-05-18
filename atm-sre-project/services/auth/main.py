import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
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
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

app = FastAPI(title="Auth Service")
Instrumentator().instrument(app).expose(app)

bearer_scheme = HTTPBearer()

redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


class LoginRequest(BaseModel):
    account_number: str
    pin: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_token(user_id: int, account_number: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "account_number": account_number,
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


@app.get("/health")
def health():
    return {"status": "ok", "service": "auth"}


@app.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        "SELECT id, pin_hash FROM users WHERE account_number = %s",
        (body.account_number,),
    )
    row = cur.fetchone()
    if not row or not bcrypt.checkpw(body.pin.encode(), row[1].encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_token(user_id=row[0], account_number=body.account_number)
    return {"access_token": token}


@app.post("/auth/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    jti = payload.get("jti")
    exp = payload.get("exp")
    ttl = max(0, int(exp - datetime.now(timezone.utc).timestamp()))
    if jti and ttl > 0:
        redis_client.setex(f"blacklist:{jti}", ttl, "1")
    return {"detail": "Logged out"}


@app.post("/auth/validate")
def validate_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    jti = payload.get("jti")
    if jti and redis_client.exists(f"blacklist:{jti}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    return {
        "user_id": payload["sub"],
        "account_number": payload["account_number"],
    }
