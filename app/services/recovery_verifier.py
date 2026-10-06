from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.dependency import ServiceDependency
from app.models.incident import Incident
from app.models.log import LogEvent
from app.models.metric import MetricSample
from app.models.recovery_check import RecoveryCheck
from app.models.service import Service
from app.models.telemetry import TelemetryEvent


@dataclass
class RecoveryCheckResult:
    check_type: str
    service_id: str
    status: str
    expected_value: float | None
    observed_value: float | None
    details: str


class RecoveryVerifier:
    """
    Deterministic recovery verification engine.

    It validates whether the affected service has recovered
    after remediation using recent telemetry and metrics.
    """

    DEFAULT_WINDOW_SECONDS = 120

    LATENCY_THRESHOLD_MS = 500.0
    ERROR_RATE_THRESHOLD_PERCENT = 1.0
    QUEUE_BACKLOG_THRESHOLD = 100.0

    def _normalize_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    def check_service_health(
        self,
        db: Session,
        service_id: str,
    ) -> RecoveryCheckResult:
        service = (
            db.query(Service)
            .filter(Service.service_id == service_id)
            .first()
        )

        if service is None:
            return RecoveryCheckResult(
                check_type="SERVICE_HEALTH",
                service_id=service_id,
                status="FAILED",
                expected_value=1.0,
                observed_value=0.0,
                details="Service does not exist in the SentinelAI service registry.",
            )

        observed = 1.0 if service.is_active else 0.0

        if service.is_active:
            return RecoveryCheckResult(
                check_type="SERVICE_HEALTH",
                service_id=service_id,
                status="PASSED",
                expected_value=1.0,
                observed_value=observed,
                details="Service is active in the service registry.",
            )

        return RecoveryCheckResult(
            check_type="SERVICE_HEALTH",
            service_id=service_id,
            status="FAILED",
            expected_value=1.0,
            observed_value=observed,
            details="Service is inactive in the service registry.",
        )

    def check_latency(
        self,
        db: Session,
        service_id: str,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
    ) -> RecoveryCheckResult:
        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=window_seconds
        )

        average_latency = (
            db.query(func.avg(MetricSample.value))
            .filter(
                MetricSample.service_id == service_id,
                MetricSample.metric_name.in_(
                    [
                        "latency_ms",
                        "request_latency_ms",
                        "http_latency_ms",
                    ]
                ),
                MetricSample.timestamp >= cutoff,
            )
            .scalar()
        )

        if average_latency is None:
            telemetry_average = (
                db.query(func.avg(TelemetryEvent.latency_ms))
                .filter(
                    TelemetryEvent.service_id == service_id,
                    TelemetryEvent.timestamp >= cutoff,
                )
                .scalar()
            )

            average_latency = telemetry_average

        if average_latency is None:
            return RecoveryCheckResult(
                check_type="LATENCY",
                service_id=service_id,
                status="INCONCLUSIVE",
                expected_value=self.LATENCY_THRESHOLD_MS,
                observed_value=None,
                details="No recent latency telemetry was available.",
            )

        average_latency = float(average_latency)

        if average_latency <= self.LATENCY_THRESHOLD_MS:
            status = "PASSED"
            details = (
                f"Observed average latency {average_latency:.2f} ms "
                f"is within the recovery threshold of "
                f"{self.LATENCY_THRESHOLD_MS:.2f} ms."
            )
        else:
            status = "FAILED"
            details = (
                f"Observed average latency {average_latency:.2f} ms "
                f"exceeds the recovery threshold of "
                f"{self.LATENCY_THRESHOLD_MS:.2f} ms."
            )

        return RecoveryCheckResult(
            check_type="LATENCY",
            service_id=service_id,
            status=status,
            expected_value=self.LATENCY_THRESHOLD_MS,
            observed_value=average_latency,
            details=details,
        )

    def check_error_rate(
        self,
        db: Session,
        service_id: str,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
    ) -> RecoveryCheckResult:
        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=window_seconds
        )

        total_requests = (
            db.query(func.count(TelemetryEvent.id))
            .filter(
                TelemetryEvent.service_id == service_id,
                TelemetryEvent.timestamp >= cutoff,
            )
            .scalar()
        )

        failed_requests = (
            db.query(func.count(TelemetryEvent.id))
            .filter(
                TelemetryEvent.service_id == service_id,
                TelemetryEvent.timestamp >= cutoff,
                TelemetryEvent.success.is_(False),
            )
            .scalar()
        )

        total_requests = int(total_requests or 0)
        failed_requests = int(failed_requests or 0)

        if total_requests == 0:
            return RecoveryCheckResult(
                check_type="ERROR_RATE",
                service_id=service_id,
                status="INCONCLUSIVE",
                expected_value=self.ERROR_RATE_THRESHOLD_PERCENT,
                observed_value=None,
                details="No recent telemetry requests were available.",
            )

        error_rate = (
            failed_requests / total_requests
        ) * 100.0

        if error_rate <= self.ERROR_RATE_THRESHOLD_PERCENT:
            status = "PASSED"
            details = (
                f"Observed error rate {error_rate:.2f}% "
                f"is within the recovery threshold of "
                f"{self.ERROR_RATE_THRESHOLD_PERCENT:.2f}%."
            )
        else:
            status = "FAILED"
            details = (
                f"Observed error rate {error_rate:.2f}% "
                f"exceeds the recovery threshold of "
                f"{self.ERROR_RATE_THRESHOLD_PERCENT:.2f}%."
            )

        return RecoveryCheckResult(
            check_type="ERROR_RATE",
            service_id=service_id,
            status=status,
            expected_value=self.ERROR_RATE_THRESHOLD_PERCENT,
            observed_value=error_rate,
            details=details,
        )

    def check_dependencies(
        self,
        db: Session,
        service_id: str,
    ) -> RecoveryCheckResult:
        dependencies = (
            db.query(ServiceDependency)
            .filter(
                (
                    ServiceDependency.source_service_id == service_id
                )
                | (
                    ServiceDependency.target_service_id == service_id
                ),
                ServiceDependency.active.is_(True),
            )
            .all()
        )

        if not dependencies:
            return RecoveryCheckResult(
                check_type="DEPENDENCY",
                service_id=service_id,
                status="PASSED",
                expected_value=0.0,
                observed_value=0.0,
                details="No active dependencies are registered for the service.",
            )

        unhealthy_dependencies: list[str] = []

        for dependency in dependencies:
            related_service_id = (
                dependency.target_service_id
                if dependency.source_service_id == service_id
                else dependency.source_service_id
            )

            related_service = (
                db.query(Service)
                .filter(
                    Service.service_id == related_service_id
                )
                .first()
            )

            if related_service is None or not related_service.is_active:
                unhealthy_dependencies.append(
                    related_service_id
                )

        observed = float(
            len(unhealthy_dependencies)
        )

        if not unhealthy_dependencies:
            return RecoveryCheckResult(
                check_type="DEPENDENCY",
                service_id=service_id,
                status="PASSED",
                expected_value=0.0,
                observed_value=observed,
                details=(
                    f"All {len(dependencies)} registered active "
                    "dependencies are healthy."
                ),
            )

        return RecoveryCheckResult(
            check_type="DEPENDENCY",
            service_id=service_id,
            status="FAILED",
            expected_value=0.0,
            observed_value=observed,
            details=(
                "Unhealthy dependencies detected: "
                + ", ".join(unhealthy_dependencies)
            ),
        )

    def check_queue_backlog(
        self,
        db: Session,
        service_id: str,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
    ) -> RecoveryCheckResult:
        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=window_seconds
        )

        queue_metric = (
            db.query(MetricSample)
            .filter(
                MetricSample.service_id == service_id,
                MetricSample.timestamp >= cutoff,
                MetricSample.metric_name.in_(
                    [
                        "queue_depth",
                        "queue_backlog",
                        "queue_size",
                    ]
                ),
            )
            .order_by(MetricSample.timestamp.desc())
            .first()
        )

        if queue_metric is None:
            return RecoveryCheckResult(
                check_type="QUEUE_BACKLOG",
                service_id=service_id,
                status="INCONCLUSIVE",
                expected_value=self.QUEUE_BACKLOG_THRESHOLD,
                observed_value=None,
                details="No recent queue backlog metric was available.",
            )

        observed = float(queue_metric.value)

        if observed <= self.QUEUE_BACKLOG_THRESHOLD:
            status = "PASSED"
            details = (
                f"Observed queue backlog {observed:.2f} "
                f"is within the recovery threshold of "
                f"{self.QUEUE_BACKLOG_THRESHOLD:.2f}."
            )
        else:
            status = "FAILED"
            details = (
                f"Observed queue backlog {observed:.2f} "
                f"exceeds the recovery threshold of "
                f"{self.QUEUE_BACKLOG_THRESHOLD:.2f}."
            )

        return RecoveryCheckResult(
            check_type="QUEUE_BACKLOG",
            service_id=service_id,
            status=status,
            expected_value=self.QUEUE_BACKLOG_THRESHOLD,
            observed_value=observed,
            details=details,
        )

    def run_checks(
        self,
        db: Session,
        incident: Incident,
        remediation_action_id: int | None = None,
    ) -> list[RecoveryCheckResult]:
        service_id = incident.service_id

        results = [
            self.check_service_health(
                db,
                service_id,
            ),
            self.check_latency(
                db,
                service_id,
            ),
            self.check_error_rate(
                db,
                service_id,
            ),
            self.check_dependencies(
                db,
                service_id,
            ),
            self.check_queue_backlog(
                db,
                service_id,
            ),
        ]

        for result in results:
            db.add(
                RecoveryCheck(
                    incident_id=incident.id,
                    remediation_action_id=remediation_action_id,
                    service_id=result.service_id,
                    check_type=result.check_type,
                    expected_value=result.expected_value,
                    observed_value=result.observed_value,
                    status=result.status,
                    details=result.details,
                )
            )

        db.commit()

        return results

    def summarize(
        self,
        results: list[RecoveryCheckResult],
    ) -> str:
        if not results:
            return "INCONCLUSIVE"

        if any(
            result.status == "FAILED"
            for result in results
        ):
            return "FAILED"

        if all(
            result.status == "PASSED"
            for result in results
        ):
            return "PASSED"

        return "INCONCLUSIVE"

    def get_status(
        self,
        db: Session,
        incident_id: int,
    ) -> str:
        checks = (
            db.query(RecoveryCheck)
            .filter(
                RecoveryCheck.incident_id == incident_id
            )
            .order_by(
                RecoveryCheck.checked_at.desc()
            )
            .all()
        )

        if not checks:
            return "INCONCLUSIVE"

        latest_by_type: dict[str, RecoveryCheck] = {}

        for check in checks:
            if check.check_type not in latest_by_type:
                latest_by_type[check.check_type] = check

        latest = list(latest_by_type.values())

        if any(
            check.status == "FAILED"
            for check in latest
        ):
            return "FAILED"

        if all(
            check.status == "PASSED"
            for check in latest
        ):
            return "PASSED"

        return "INCONCLUSIVE"


recovery_verifier = RecoveryVerifier()