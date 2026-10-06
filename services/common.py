import random
import time
import uuid

from fastapi import Header, HTTPException

from services.config import (
    DEFAULT_FAILURE_RATE,
    DEFAULT_LATENCY_MS,
)


def get_request_id(
    x_request_id: str | None = Header(default=None),
) -> str:
    return x_request_id or str(uuid.uuid4())


def simulate_failure_and_latency(
    latency_ms: int = DEFAULT_LATENCY_MS,
    failure_rate: float = DEFAULT_FAILURE_RATE,
) -> None:
    if latency_ms > 0:
        time.sleep(latency_ms / 1000)

    if failure_rate > 0 and random.random() < failure_rate:
        raise HTTPException(
            status_code=503,
            detail="Injected service failure.",
        )


def now_ms(start: float) -> float:
    return round(
        (time.perf_counter() - start) * 1000,
        2,
    )