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


INVENTORY_LATENCY_MS = int(
    os.getenv("INVENTORY_LATENCY_MS", "0")
)

INVENTORY_FAILURE_RATE = float(
    os.getenv("INVENTORY_FAILURE_RATE", "0")
)


app = FastAPI(
    title="SentinelAI Inventory Service",
    version="1.0.0",
)

app.add_middleware(
    TelemetryMiddleware,
    service_id="inventory-service",
)


@app.get("/health")
def health():
    return {
        "service": "inventory-service",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/ready")
def ready():
    return {
        "service": "inventory-service",
        "ready": True,
    }


@app.post("/reserve")
def reserve_inventory(
    payload: dict,
    x_request_id: str | None = Header(default=None),
):
    request_id = get_request_id(x_request_id)

    start = time.perf_counter()

    simulate_failure_and_latency(
        latency_ms=INVENTORY_LATENCY_MS,
        failure_rate=INVENTORY_FAILURE_RATE,
    )

    reservation_id = (
        f"res-{uuid.uuid4().hex[:12]}"
    )

    return {
        "reservation_id": reservation_id,
        "status": "reserved",
        "product_id": payload.get(
            "product_id",
            "product-001",
        ),
        "quantity": int(
            payload.get("quantity", 1)
        ),
        "request_id": request_id,
        "latency_ms": now_ms(start),
    }