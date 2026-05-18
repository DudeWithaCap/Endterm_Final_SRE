import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal

import redis
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorClient
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
MONGO_DB = os.getenv("MONGO_DB", "bankdb")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"

redis_client = redis.from_url(REDIS_URL, decode_responses=True)
bearer_scheme = HTTPBearer()

db_client: AsyncIOMotorClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client
    db_client = AsyncIOMotorClient(MONGO_URL)
    # Create indexes on startup for efficient querying
    col = db_client[MONGO_DB]["transactions"]
    await col.create_index("from_account")
    await col.create_index("to_account")
    await col.create_index("created_at")
    await col.create_index([("from_account", 1), ("created_at", -1)])
    await col.create_index([("to_account", 1), ("created_at", -1)])
    yield
    db_client.close()


app = FastAPI(title="Transaction History Service", lifespan=lifespan)
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


def get_collection():
    return db_client[MONGO_DB]["transactions"]


# ── Models ────────────────────────────────────────────────────────────────────

class TransactionEvent(BaseModel):
    transaction_id: int
    type: Literal["deposit", "withdraw", "transfer"]
    from_account: str | None = None
    to_account: str | None = None
    amount: float
    status: Literal["success", "failed"]
    created_at: str


class TransactionRecord(BaseModel):
    id: str = Field(alias="_id")
    transaction_id: int
    type: str
    from_account: str | None
    to_account: str | None
    amount: float
    status: str
    created_at: str

    model_config = {"populate_by_name": True}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "history"}


@app.post("/history/events", status_code=201)
async def ingest_event(event: TransactionEvent):
    """Internal endpoint — called by Transaction Service only. No auth required."""
    col = get_collection()
    doc = event.model_dump()
    doc["ingested_at"] = datetime.now(timezone.utc).isoformat()
    await col.insert_one(doc)
    return {"detail": "recorded"}


@app.get("/history/{account_number}")
async def get_history(
    account_number: str,
    auth=Depends(require_auth),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tx_type: str | None = Query(None, alias="type"),
    date_from: str | None = Query(None, description="ISO 8601 date, e.g. 2024-01-01"),
    date_to: str | None = Query(None, description="ISO 8601 date, e.g. 2024-12-31"),
):
    col = get_collection()

    query: dict = {
        "$or": [
            {"from_account": account_number},
            {"to_account": account_number},
        ]
    }

    if tx_type:
        query["type"] = tx_type

    if date_from or date_to:
        date_filter: dict = {}
        if date_from:
            date_filter["$gte"] = date_from
        if date_to:
            date_filter["$lte"] = date_to + "T23:59:59"
        query["created_at"] = date_filter

    skip = (page - 1) * page_size
    cursor = col.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(page_size)
    records = await cursor.to_list(length=page_size)
    total = await col.count_documents(query)

    return {
        "account_number": account_number,
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": records,
    }
