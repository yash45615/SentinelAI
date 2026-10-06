import os
import time
import uuid

import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


TELEMETRY_URL = os.getenv(
    "TELEMETRY_URL",
    "http://127.0.0.1:8000/telemetry",
)

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "production",
)


class TelemetryMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, service_id: str):
        super().__init__(app)
        self.service_id = service_id

    async def dispatch(self, request: Request, call_next):

        start = time.perf_counter()

        request_id = request.headers.get(
            "X-Request-ID"
        ) or str(uuid.uuid4())

        trace_id = request.headers.get(
            "X-Trace-ID"
        ) or str(uuid.uuid4())

        status_code = 500
        error_type = None
        error_message = None

        try:
            response = await call_next(request)

            status_code = response.status_code

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id

            return response

        except Exception as exc:
            error_type = type(exc).__name__
            error_message = str(exc)

            raise

        finally:

            latency_ms = round(
                (time.perf_counter() - start) * 1000,
                2,
            )

            telemetry = {
                "request_id": request_id,
                "trace_id": trace_id,
                "service_id": self.service_id,
                "environment": ENVIRONMENT,
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": status_code,
                "latency_ms": latency_ms,
                "success": status_code < 500,
                "error_type": error_type,
                "error_message": error_message,
            }

            try:
                async with httpx.AsyncClient(timeout=1.0) as client:
                    await client.post(
                        TELEMETRY_URL,
                        json=telemetry,
                    )
            except Exception:
                # Telemetry must never take down the production service.
                pass