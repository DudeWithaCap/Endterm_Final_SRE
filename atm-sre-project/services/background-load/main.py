import asyncio
import os
import random
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

load_dotenv()

INTERVAL = float(os.getenv("LOAD_INTERVAL_SECONDS", "5"))
LATENCY_SPIKE_EVERY = int(os.getenv("LATENCY_SPIKE_EVERY", "30"))

# ── Prometheus metrics ────────────────────────────────────────────────────────

load_ops_total = Counter(
    "background_load_ops_total",
    "Total synthetic operations",
    ["operation", "status"],
)
load_latency = Histogram(
    "background_load_op_duration_seconds",
    "Simulated duration of each synthetic operation",
    ["operation"],
)

# ── Operation weights ─────────────────────────────────────────────────────────

# (weight, name, success_rate)
OPERATIONS = [
    (40, "deposit",   0.99),
    (40, "withdraw",  0.96),  # occasional insufficient-funds failures
    (15, "transfer",  0.97),
    (5,  "bad_auth",  0.0),   # always fails — drives error-rate metric
]
_weights = [w for w, _, _ in OPERATIONS]
_ops     = [(n, r) for _, n, r in OPERATIONS]

_op_count = 0


async def load_loop():
    global _op_count
    while True:
        await asyncio.sleep(INTERVAL)
        _op_count += 1

        name, success_rate = random.choices(_ops, weights=_weights, k=1)[0]

        # Simulate occasional latency spike
        base_latency = random.uniform(0.01, 0.15)
        if _op_count % LATENCY_SPIKE_EVERY == 0:
            base_latency += 0.5

        # Simulate operation duration
        await asyncio.sleep(base_latency)

        status = "success" if random.random() < success_rate else "error"
        load_ops_total.labels(operation=name, status=status).inc()
        load_latency.labels(operation=name).observe(base_latency)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(load_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Background Load Service", lifespan=lifespan)
Instrumentator().instrument(app).expose(app)


@app.get("/health")
def health():
    return {"status": "ok", "service": "background-load"}


@app.get("/load/stats")
def stats():
    return {
        "ops_fired": _op_count,
        "interval_seconds": INTERVAL,
        "latency_spike_every": LATENCY_SPIKE_EVERY,
    }
