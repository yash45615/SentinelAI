from datetime import datetime, timedelta, timezone
from statistics import quantiles

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.recovery_check import RecoveryCheck
from app.models.slo_result import SloResult
from app.models.telemetry import TelemetryEvent


class SloEngine:
    AVAILABILITY_TARGET = 99.9
    ERROR_RATE_TARGET = 1.0
    P95_LATENCY_TARGET_MS = 500.0
    DETECTION_TARGET_SECONDS = 30.0
    RECOVERY_TARGET_SECONDS = 60.0

    def _utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _percentile_95(
        self,
        values: list[float],
    ) -> float:
        if not values:
            return 0.0

        if len(values) == 1:
            return float(values[0])

        values = sorted(values)

        try:
            return float(
                quantiles(
                    values,
                    n=100,
                    method="inclusive",
                )[94]
            )
        except Exception:
            index = int(
                round((len(values) - 1) * 0.95)
            )
            return float(values[index])

    def calculate_availability(
        self,
        total_requests: int,
        successful_requests: int,
    ) -> float:
        if total_requests <= 0:
            return 100.0

        return (
            successful_requests
            / total_requests
        ) * 100.0

    def calculate_error_rate(
        self,
        total_requests: int,
        failed_requests: int,
    ) -> float:
        if total_requests <= 0:
            return 0.0

        return (
            failed_requests
            / total_requests
        ) * 100.0

    def calculate_error_budget(
        self,
        availability: float,
        target: float = AVAILABILITY_TARGET,
    ) -> tuple[float, float]:
        allowed_failure_percent = 100.0 - target

        if allowed_failure_percent <= 0:
            return 0.0, 0.0

        actual_failure_percent = max(
            0.0,
            100.0 - availability,
        )

        remaining = max(
            0.0,
            allowed_failure_percent
            - actual_failure_percent,
        )

        remaining_percent = (
            remaining
            / allowed_failure_percent
        ) * 100.0

        consumed_percent = max(
            0.0,
            min(
                100.0,
                (
                    actual_failure_percent
                    / allowed_failure_percent
                ) * 100.0,
            ),
        )

        return (
            allowed_failure_percent,
            remaining_percent,
        )

    def calculate_burn_rate(
        self,
        availability: float,
        target: float = AVAILABILITY_TARGET,
    ) -> float:
        allowed_failure = 100.0 - target

        if allowed_failure <= 0:
            return 0.0

        actual_failure = max(
            0.0,
            100.0 - availability,
        )

        return actual_failure / allowed_failure

    def calculate_detection_time(
        self,
        incident: Incident,
    ) -> float | None:
        if incident.acknowledged_at is None:
            return None

        detected_at = incident.detected_at
        acknowledged_at = incident.acknowledged_at

        if detected_at.tzinfo is None:
            detected_at = detected_at.replace(
                tzinfo=timezone.utc
            )

        if acknowledged_at.tzinfo is None:
            acknowledged_at = acknowledged_at.replace(
                tzinfo=timezone.utc
            )

        return max(
            0.0,
            (
                acknowledged_at
                - detected_at
            ).total_seconds(),
        )

    def calculate_recovery_time(
        self,
        incident: Incident,
    ) -> float | None:
        if incident.resolved_at is None:
            return None

        detected_at = incident.detected_at
        resolved_at = incident.resolved_at

        if detected_at.tzinfo is None:
            detected_at = detected_at.replace(
                tzinfo=timezone.utc
            )

        if resolved_at.tzinfo is None:
            resolved_at = resolved_at.replace(
                tzinfo=timezone.utc
            )

        return max(
            0.0,
            (
                resolved_at
                - detected_at
            ).total_seconds(),
        )

    def determine_status(
        self,
        availability_met: bool,
        error_rate_met: bool,
        latency_met: bool,
        detection_met: bool | None,
        recovery_met: bool | None,
    ) -> str:
        mandatory = [
            availability_met,
            error_rate_met,
            latency_met,
        ]

        if not all(mandatory):
            return "BREACHED"

        optional_checks = [
            detection_met,
            recovery_met,
        ]

        if any(
            value is False
            for value in optional_checks
        ):
            return "AT_RISK"

        if any(
            value is None
            for value in optional_checks
        ):
            return "HEALTHY_WITHOUT_FULL_DATA"

        return "HEALTHY"

    def calculate_service_slo(
        self,
        db: Session,
        service_id: str,
        window_minutes: int = 60,
        environment: str = "production",
    ) -> SloResult:
        if window_minutes <= 0:
            raise ValueError(
                "window_minutes must be greater than zero."
            )

        now = self._utc_now()

        cutoff = now - timedelta(
            minutes=window_minutes
        )

        telemetry = (
            db.query(TelemetryEvent)
            .filter(
                TelemetryEvent.service_id == service_id,
                TelemetryEvent.environment == environment,
                TelemetryEvent.timestamp >= cutoff,
                TelemetryEvent.timestamp <= now,
            )
            .all()
        )

        total_requests = len(telemetry)

        successful_requests = sum(
            1
            for event in telemetry
            if event.success
        )

        failed_requests = (
            total_requests
            - successful_requests
        )

        availability = (
            self.calculate_availability(
                total_requests,
                successful_requests,
            )
        )

        error_rate = (
            self.calculate_error_rate(
                total_requests,
                failed_requests,
            )
        )

        latencies = [
            float(event.latency_ms)
            for event in telemetry
            if event.latency_ms is not None
        ]

        p95_latency = self._percentile_95(
            latencies
        )

        availability_met = (
            availability
            >= self.AVAILABILITY_TARGET
        )

        error_rate_met = (
            error_rate
            <= self.ERROR_RATE_TARGET
        )

        latency_met = (
            p95_latency
            < self.P95_LATENCY_TARGET_MS
        )

        incident = (
            db.query(Incident)
            .filter(
                Incident.service_id == service_id,
                Incident.environment == environment,
                Incident.detected_at >= cutoff,
                Incident.detected_at <= now,
            )
            .order_by(
                Incident.detected_at.desc()
            )
            .first()
        )

        detection_actual = None

        if incident is not None:
            detection_actual = (
                self.calculate_detection_time(
                    incident
                )
            )

        detection_met = (
            None
            if detection_actual is None
            else detection_actual
            <= self.DETECTION_TARGET_SECONDS
        )

        recovery_actual = None

        if incident is not None:
            recovery_actual = (
                self.calculate_recovery_time(
                    incident
                )
            )

        recovery_met = (
            None
            if recovery_actual is None
            else recovery_actual
            <= self.RECOVERY_TARGET_SECONDS
        )

        (
            error_budget_percent,
            error_budget_remaining_percent,
        ) = self.calculate_error_budget(
            availability
        )

        burn_rate = self.calculate_burn_rate(
            availability
        )

        overall_status = self.determine_status(
            availability_met,
            error_rate_met,
            latency_met,
            detection_met,
            recovery_met,
        )

        result = SloResult(
            service_id=service_id,
            environment=environment,
            window_minutes=window_minutes,
            availability_target=self.AVAILABILITY_TARGET,
            availability_actual=availability,
            error_rate_target=self.ERROR_RATE_TARGET,
            error_rate_actual=error_rate,
            p95_latency_target_ms=(
                self.P95_LATENCY_TARGET_MS
            ),
            p95_latency_actual_ms=p95_latency,
            detection_target_seconds=(
                self.DETECTION_TARGET_SECONDS
            ),
            detection_actual_seconds=detection_actual,
            recovery_target_seconds=(
                self.RECOVERY_TARGET_SECONDS
            ),
            recovery_actual_seconds=recovery_actual,
            availability_met=availability_met,
            error_rate_met=error_rate_met,
            latency_met=latency_met,
            detection_met=detection_met,
            recovery_met=recovery_met,
            overall_status=overall_status,
            error_budget_percent=error_budget_percent,
            error_budget_remaining_percent=(
                error_budget_remaining_percent
            ),
            burn_rate=burn_rate,
        )

        db.add(result)
        db.commit()
        db.refresh(result)

        return result

    def get_latest(
        self,
        db: Session,
        service_id: str,
    ) -> SloResult | None:
        return (
            db.query(SloResult)
            .filter(
                SloResult.service_id == service_id
            )
            .order_by(
                SloResult.calculated_at.desc()
            )
            .first()
        )


slo_engine = SloEngine()