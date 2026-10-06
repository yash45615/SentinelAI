import os
import time
import uuid

from fastapi import FastAPI, Header

from services.common import (
    get_request_id,
    now_ms,
    simulate_failure_and_latency,
)
from services.telemetry import TelemetryMiddleware


PAYMENTS_LATENCY_MS = int(
    os.getenv("PAYMENTS_LATENCY_MS", "0")
)

PAYMENTS_FAILURE_RATE = float(
    os.getenv("PAYMENTS_FAILURE_RATE", "0")
)


app = FastAPI(
    title="SentinelAI Payments Service",
    version="1.0.0",
)

app.add_middleware(
    TelemetryMiddleware,
    service_id="payments-service",
)


@app.get("/health")
def health():
    return {
        "service": "payments-service",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/ready")
def ready():
    return {
        "service": "payments-service",
        "ready": True,
    }


@app.post("/authorize")
def authorize_payment(
    payload: dict,
    x_request_id: str | None = Header(default=None),
):
    request_id = get_request_id(x_request_id)

    start = time.perf_counter()

    simulate_failure_and_latency(
        latency_ms=PAYMENTS_LATENCY_MS,
        failure_rate=PAYMENTS_FAILURE_RATE,
    )

    amount = float(
        payload.get("amount", 100)
    )

    payment_id = (
        f"pay-{uuid.uuid4().hex[:12]}"
    )

    return {
        "payment_id": payment_id,
        "status": "authorized",
        "amount": amount,
        "request_id": request_id,
        "latency_ms": now_ms(start),
    }