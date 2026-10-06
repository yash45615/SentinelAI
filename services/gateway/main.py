import os
import time
import uuid

import httpx
from fastapi import FastAPI, Header, HTTPException

from services.common import now_ms
from services.telemetry import TelemetryMiddleware


ORDERS_URL = os.getenv(
    "ORDERS_URL",
    "http://127.0.0.1:8101",
)

REQUEST_TIMEOUT_SECONDS = float(
    os.getenv("REQUEST_TIMEOUT_SECONDS", "3")
)


app = FastAPI(
    title="SentinelAI API Gateway",
    version="1.0.0",
)

app.add_middleware(
    TelemetryMiddleware,
    service_id="api-gateway",
)


@app.get("/health")
def health():
    return {
        "service": "api-gateway",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/ready")
def ready():
    return {
        "service": "api-gateway",
        "ready": True,
    }


@app.post("/orders")
async def create_order(
    payload: dict,
    x_request_id: str | None = Header(default=None),
):
    request_id = x_request_id or str(uuid.uuid4())

    start = time.perf_counter()

    headers = {
        "X-Request-ID": request_id,
    }

    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT_SECONDS
        ) as client:

            response = await client.post(
                f"{ORDERS_URL}/orders",
                json=payload,
                headers=headers,
            )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Orders service timeout.",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Orders service unavailable.",
        )

    duration_ms = now_ms(start)

    if response.status_code >= 500:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Orders service failed.",
                "request_id": request_id,
                "upstream_status": response.status_code,
                "latency_ms": duration_ms,
            },
        )

    return {
        "gateway": "api-gateway",
        "request_id": request_id,
        "latency_ms": duration_ms,
        "upstream": response.json(),
    }