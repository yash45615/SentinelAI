import os
import time
import uuid

import httpx
from fastapi import FastAPI, Header, HTTPException

from services.common import (
    get_request_id,
    now_ms,
    simulate_failure_and_latency,
)
from services.telemetry import TelemetryMiddleware


PAYMENTS_URL = os.getenv(
    "PAYMENTS_URL",
    "http://127.0.0.1:8102",
)

INVENTORY_URL = os.getenv(
    "INVENTORY_URL",
    "http://127.0.0.1:8103",
)

NOTIFICATIONS_URL = os.getenv(
    "NOTIFICATIONS_URL",
    "http://127.0.0.1:8104",
)

REQUEST_TIMEOUT_SECONDS = float(
    os.getenv("REQUEST_TIMEOUT_SECONDS", "3")
)

ORDERS_LATENCY_MS = int(
    os.getenv("ORDERS_LATENCY_MS", "0")
)

ORDERS_FAILURE_RATE = float(
    os.getenv("ORDERS_FAILURE_RATE", "0")
)


app = FastAPI(
    title="SentinelAI Orders Service",
    version="1.0.0",
)

app.add_middleware(
    TelemetryMiddleware,
    service_id="orders-service",
)


@app.get("/health")
def health():
    return {
        "service": "orders-service",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/ready")
def ready():
    return {
        "service": "orders-service",
        "ready": True,
    }


@app.post("/orders")
async def create_order(
    payload: dict,
    x_request_id: str | None = Header(default=None),
):
    request_id = get_request_id(x_request_id)

    simulate_failure_and_latency(
        latency_ms=ORDERS_LATENCY_MS,
        failure_rate=ORDERS_FAILURE_RATE,
    )

    start = time.perf_counter()

    product_id = payload.get(
        "product_id",
        "product-001",
    )

    quantity = int(
        payload.get("quantity", 1)
    )

    amount = float(
        payload.get("amount", 100)
    )

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT_SECONDS
    ) as client:

        inventory_response = await client.post(
            f"{INVENTORY_URL}/reserve",
            json={
                "product_id": product_id,
                "quantity": quantity,
            },
            headers={
                "X-Request-ID": request_id,
            },
        )

        if inventory_response.status_code >= 500:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Inventory dependency failed.",
                    "request_id": request_id,
                },
            )

        payment_response = await client.post(
            f"{PAYMENTS_URL}/authorize",
            json={
                "amount": amount,
            },
            headers={
                "X-Request-ID": request_id,
            },
        )

        if payment_response.status_code >= 500:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Payment dependency failed.",
                    "request_id": request_id,
                },
            )

        notification_response = await client.post(
            f"{NOTIFICATIONS_URL}/send",
            json={
                "event": "order_created",
                "request_id": request_id,
            },
            headers={
                "X-Request-ID": request_id,
            },
        )

        notification_status = (
            "sent"
            if notification_response.status_code < 500
            else "failed"
        )

    order_id = (
        f"ord-{uuid.uuid4().hex[:12]}"
    )

    return {
        "order_id": order_id,
        "status": "created",
        "request_id": request_id,
        "inventory": inventory_response.json(),
        "payment": payment_response.json(),
        "notification_status": notification_status,
        "latency_ms": now_ms(start),
    }