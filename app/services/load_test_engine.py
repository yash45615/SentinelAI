import asyncio
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

import httpx


@dataclass
class LoadTestResultData:
    test_id: str
    service_id: str
    endpoint: str
    concurrency: int
    duration_seconds: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate_percent: float
    performance_status: str
    gate_reason: str
    started_at: datetime
    completed_at: datetime


class LoadTestEngine:
    MAX_CONCURRENCY = 100
    MAX_DURATION_SECONDS = 300

    P95_LATENCY_LIMIT_MS = 500.0
    ERROR_RATE_LIMIT_PERCENT = 1.0

    def validate_parameters(
        self,
        concurrency: int,
        duration_seconds: int,
    ) -> None:
        if concurrency <= 0:
            raise ValueError(
                "concurrency must be greater than zero."
            )

        if concurrency > self.MAX_CONCURRENCY:
            raise ValueError(
                f"concurrency cannot exceed "
                f"{self.MAX_CONCURRENCY}."
            )

        if duration_seconds <= 0:
            raise ValueError(
                "duration_seconds must be greater than zero."
            )

        if duration_seconds > self.MAX_DURATION_SECONDS:
            raise ValueError(
                f"duration_seconds cannot exceed "
                f"{self.MAX_DURATION_SECONDS}."
            )

    def percentile(
        self,
        values: list[float],
        percentile: float,
    ) -> float:
        if not values:
            return 0.0

        values = sorted(values)

        if len(values) == 1:
            return float(values[0])

        position = (
            percentile / 100.0
        ) * (len(values) - 1)

        lower = int(position)
        upper = min(
            lower + 1,
            len(values) - 1,
        )

        weight = position - lower

        return (
            values[lower]
            + (
                values[upper]
                - values[lower]
            )
            * weight
        )

    def evaluate_gate(
        self,
        p95_latency_ms: float,
        error_rate_percent: float,
    ) -> tuple[str, str]:
        failures = []

        if p95_latency_ms > self.P95_LATENCY_LIMIT_MS:
            failures.append(
                f"P95 latency {p95_latency_ms:.2f} ms "
                f"exceeded {self.P95_LATENCY_LIMIT_MS:.2f} ms"
            )

        if error_rate_percent > self.ERROR_RATE_LIMIT_PERCENT:
            failures.append(
                f"error rate {error_rate_percent:.2f}% "
                f"exceeded {self.ERROR_RATE_LIMIT_PERCENT:.2f}%"
            )

        if failures:
            return (
                "FAILED",
                "; ".join(failures),
            )

        return (
            "PASSED",
            "Latency and error-rate performance gates passed.",
        )

    async def _request(
        self,
        client: httpx.AsyncClient,
        url: str,
    ) -> tuple[bool, float]:
        started = time.perf_counter()

        try:
            response = await client.get(
                url,
                timeout=10.0,
            )

            latency_ms = (
                time.perf_counter()
                - started
            ) * 1000.0

            return (
                200 <= response.status_code < 500,
                latency_ms,
            )

        except Exception:
            latency_ms = (
                time.perf_counter()
                - started
            ) * 1000.0

            return False, latency_ms

    async def run(
        self,
        base_url: str,
        service_id: str,
        endpoint: str,
        concurrency: int,
        duration_seconds: int,
    ) -> LoadTestResultData:
        self.validate_parameters(
            concurrency,
            duration_seconds,
        )

        if not base_url:
            raise ValueError(
                "base_url cannot be empty."
            )

        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint

        url = (
            base_url.rstrip("/")
            + endpoint
        )

        test_id = (
            f"LOAD-{uuid4().hex[:12].upper()}"
        )

        started_at = datetime.now(
            timezone.utc
        )

        latencies: list[float] = []
        successful_requests = 0
        failed_requests = 0

        stop_time = (
            time.monotonic()
            + duration_seconds
        )

        semaphore = asyncio.Semaphore(
            concurrency
        )

        async with httpx.AsyncClient() as client:

            async def worker():
                nonlocal successful_requests
                nonlocal failed_requests

                while time.monotonic() < stop_time:
                    async with semaphore:
                        success, latency = (
                            await self._request(
                                client,
                                url,
                            )
                        )

                    latencies.append(
                        latency
                    )

                    if success:
                        successful_requests += 1
                    else:
                        failed_requests += 1

            workers = [
                asyncio.create_task(worker())
                for _ in range(concurrency)
            ]

            await asyncio.gather(*workers)

        completed_at = datetime.now(
            timezone.utc
        )

        total_requests = (
            successful_requests
            + failed_requests
        )

        elapsed_seconds = max(
            0.001,
            (
                completed_at
                - started_at
            ).total_seconds(),
        )

        requests_per_second = (
            total_requests
            / elapsed_seconds
        )

        error_rate = (
            0.0
            if total_requests == 0
            else (
                failed_requests
                / total_requests
            )
            * 100.0
        )

        p50 = self.percentile(
            latencies,
            50,
        )

        p95 = self.percentile(
            latencies,
            95,
        )

        p99 = self.percentile(
            latencies,
            99,
        )

        status, reason = self.evaluate_gate(
            p95,
            error_rate,
        )

        return LoadTestResultData(
            test_id=test_id,
            service_id=service_id,
            endpoint=endpoint,
            concurrency=concurrency,
            duration_seconds=duration_seconds,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=requests_per_second,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            error_rate_percent=error_rate,
            performance_status=status,
            gate_reason=reason,
            started_at=started_at,
            completed_at=completed_at,
        )


load_test_engine = LoadTestEngine()