import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()

AUTH_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8001")
ACCOUNT_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://account:8002")
TRANSACTION_URL = os.getenv("TRANSACTION_SERVICE_URL", "http://transaction:8003")
HISTORY_URL = os.getenv("HISTORY_SERVICE_URL", "http://history:8004")
CARD_URL = os.getenv("CARD_SERVICE_URL", "http://card-management:8005")

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(title="API Gateway")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

TIMEOUT = 10.0


async def _proxy(request: Request, target_url: str) -> Response:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        url = httpx.URL(target_url)
        headers = dict(request.headers)
        headers.pop("host", None)
        body = await request.body()
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                params=request.query_params,
            )
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Upstream service unavailable")
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
            media_type=resp.headers.get("content-type"),
        )


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}


# Auth routes
@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")
async def auth_proxy(path: str, request: Request):
    return await _proxy(request, f"{AUTH_URL}/auth/{path}")


# Account routes
@app.api_route("/account/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")
async def account_proxy(path: str, request: Request):
    return await _proxy(request, f"{ACCOUNT_URL}/account/{path}")


# Transaction routes
@app.api_route("/transaction/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")
async def transaction_proxy(path: str, request: Request):
    return await _proxy(request, f"{TRANSACTION_URL}/transaction/{path}")


# History routes
@app.api_route("/history/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")
async def history_proxy(path: str, request: Request):
    return await _proxy(request, f"{HISTORY_URL}/history/{path}")


# Card management routes
@app.api_route("/card/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")
async def card_proxy(path: str, request: Request):
    return await _proxy(request, f"{CARD_URL}/card/{path}")
