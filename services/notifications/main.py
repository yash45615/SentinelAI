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


NOTIFICATIONS_LATENCY_MS = int(
    os.getenv("NOTIFICATIONS_LATENCY_MS", "0")
)

NOTIFICATIONS_FAILURE_RATE = float(
    os.getenv("NOTIFICATIONS_FAILURE_RATE", "0")
)


app = FastAPI(
    title="SentinelAI Notifications Service",
    version="1.0.0",
)

app.add_middleware(
    TelemetryMiddleware,
    service_id="notifications-service",
)


@app.get("/health")
def health():
    return {
        "service": "notifications-service",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/ready")
def ready():
    return {
        "service": "notifications-service",
        "ready": True,
    }


@app.post("/send")
def send_notification(
    payload: dict,
    x_request_id: str | None = Header(default=None),
):
    request_id = get_request_id(x_request_id)

    start = time.perf_counter()

    simulate_failure_and_latency(
        latency_ms=NOTIFICATIONS_LATENCY_MS,
        failure_rate=NOTIFICATIONS_FAILURE_RATE,
    )

    notification_id = (
        f"ntf-{uuid.uuid4().hex[:12]}"
    )

    return {
        "notification_id": notification_id,
        "status": "sent",
        "event": payload.get(
            "event",
            "unknown",
        ),
        "request_id": request_id,
        "latency_ms": now_ms(start),
    }