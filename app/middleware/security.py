import time
import uuid
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings


class SecurityMiddleware:
    """
    Lightweight application security middleware.

    Responsibilities:
    - Request ID generation/propagation
    - Security response headers
    - Optional in-memory rate limiting
    """

    def __init__(self, app):
        self.app = app
        self.request_history: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        request_id = request.headers.get(
            "X-Request-ID",
            str(uuid.uuid4()),
        )

        if settings.rate_limit_enabled:
            client = request.client.host if request.client else "unknown"
            now = time.monotonic()

            history = self.request_history[client]

            while history and (
                now - history[0]
                > settings.rate_limit_window_seconds
            ):
                history.popleft()

            if len(history) >= settings.rate_limit_requests:
                response = JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded.",
                        "request_id": request_id,
                    },
                )

                response.headers["X-Request-ID"] = request_id
                await response(scope, receive, send)
                return

            history.append(now)

        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                headers.extend(
                    [
                        (
                            b"x-request-id",
                            request_id.encode("utf-8"),
                        ),
                        (
                            b"x-content-type-options",
                            b"nosniff",
                        ),
                        (
                            b"x-frame-options",
                            b"DENY",
                        ),
                        (
                            b"referrer-policy",
                            b"no-referrer",
                        ),
                        (
                            b"permissions-policy",
                            b"geolocation=(), microphone=(), camera=()",
                        ),
                    ]
                )

                if settings.app_env.lower() == "production":
                    headers.append(
                        (
                            b"strict-transport-security",
                            b"max-age=31536000; includeSubDomains",
                        )
                    )

                message["headers"] = headers

            await send(message)

        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id

        await self.app(
            scope,
            receive,
            send_with_security_headers,
        )