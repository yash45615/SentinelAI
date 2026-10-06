from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.chaos_experiment import ChaosExperiment
from app.models.service import Service


class ChaosValidationError(ValueError):
    pass


@dataclass
class ChaosResult:
    experiment_id: str
    status: str
    failure_type: str
    target_service_id: str
    actual_effect: str


class ChaosEngine:
    ALLOWED_FAILURE_TYPES = {
        "LATENCY_INJECTION",
        "SERVICE_CRASH",
        "DB_SLOWDOWN",
        "CPU_STRESS",
        "MEMORY_PRESSURE",
        "QUEUE_BACKLOG",
        "DEPENDENCY_FAILURE",
        "BAD_DEPLOYMENT",
    }

    MAX_DURATION_SECONDS = 300
    MAX_INTENSITY = 10.0

    EXPECTED_EFFECTS = {
        "LATENCY_INJECTION": (
            "Request latency should increase for the target service."
        ),
        "SERVICE_CRASH": (
            "The target service should become unavailable."
        ),
        "DB_SLOWDOWN": (
            "Database-dependent operations should experience increased latency."
        ),
        "CPU_STRESS": (
            "CPU-related telemetry should increase for the target service."
        ),
        "MEMORY_PRESSURE": (
            "Memory utilization should increase for the target service."
        ),
        "QUEUE_BACKLOG": (
            "Queue depth should increase for the target service."
        ),
        "DEPENDENCY_FAILURE": (
            "Requests depending on the selected dependency should fail or slow down."
        ),
        "BAD_DEPLOYMENT": (
            "The target deployment should produce a measurable regression."
        ),
    }

    def validate_failure_type(
        self,
        failure_type: str,
    ) -> str:
        normalized = failure_type.upper().strip()

        if normalized not in self.ALLOWED_FAILURE_TYPES:
            raise ChaosValidationError(
                f"Unsupported failure type: {failure_type}"
            )

        return normalized

    def validate_intensity(
        self,
        intensity: float,
    ) -> float:
        if intensity <= 0:
            raise ChaosValidationError(
                "Intensity must be greater than zero."
            )

        if intensity > self.MAX_INTENSITY:
            raise ChaosValidationError(
                f"Intensity cannot exceed {self.MAX_INTENSITY}."
            )

        return float(intensity)

    def validate_duration(
        self,
        duration_seconds: int,
    ) -> int:
        if duration_seconds <= 0:
            raise ChaosValidationError(
                "Duration must be greater than zero."
            )

        if duration_seconds > self.MAX_DURATION_SECONDS:
            raise ChaosValidationError(
                f"Duration cannot exceed "
                f"{self.MAX_DURATION_SECONDS} seconds."
            )

        return duration_seconds

    def create_experiment(
        self,
        db: Session,
        target_service_id: str,
        failure_type: str,
        intensity: float,
        duration_seconds: int,
    ) -> ChaosExperiment:
        service = (
            db.query(Service)
            .filter(
                Service.service_id == target_service_id
            )
            .first()
        )

        if service is None:
            raise ChaosValidationError(
                f"Service '{target_service_id}' does not exist."
            )

        failure_type = self.validate_failure_type(
            failure_type
        )

        intensity = self.validate_intensity(
            intensity
        )

        duration_seconds = self.validate_duration(
            duration_seconds
        )

        experiment = ChaosExperiment(
            experiment_id=f"CHAOS-{uuid4().hex[:12].upper()}",
            target_service_id=target_service_id,
            failure_type=failure_type,
            intensity=intensity,
            duration_seconds=duration_seconds,
            status="PLANNED",
            expected_effect=self.EXPECTED_EFFECTS[
                failure_type
            ],
        )

        db.add(experiment)
        db.commit()
        db.refresh(experiment)

        return experiment

    def start_experiment(
        self,
        db: Session,
        experiment: ChaosExperiment,
    ) -> ChaosResult:
        if experiment.status != "PLANNED":
            raise ChaosValidationError(
                "Only PLANNED experiments can be started."
            )

        experiment.status = "RUNNING"
        experiment.started_at = datetime.now(
            timezone.utc
        )

        actual_effect = self._simulate_failure(
            experiment
        )

        experiment.actual_effect = actual_effect

        db.commit()
        db.refresh(experiment)

        return ChaosResult(
            experiment_id=experiment.experiment_id,
            status=experiment.status,
            failure_type=experiment.failure_type,
            target_service_id=experiment.target_service_id,
            actual_effect=actual_effect,
        )

    def complete_experiment(
        self,
        db: Session,
        experiment: ChaosExperiment,
        incident_created: bool = False,
        recovery_time_seconds: float | None = None,
    ) -> ChaosExperiment:
        if experiment.status != "RUNNING":
            raise ChaosValidationError(
                "Only RUNNING experiments can be completed."
            )

        experiment.status = "COMPLETED"
        experiment.completed_at = datetime.now(
            timezone.utc
        )
        experiment.incident_created = incident_created
        experiment.recovery_time_seconds = (
            recovery_time_seconds
        )

        db.commit()
        db.refresh(experiment)

        return experiment

    def fail_experiment(
        self,
        db: Session,
        experiment: ChaosExperiment,
        reason: str,
    ) -> ChaosExperiment:
        if experiment.status not in {
            "PLANNED",
            "RUNNING",
        }:
            raise ChaosValidationError(
                "Experiment cannot be failed from its current state."
            )

        experiment.status = "FAILED"
        experiment.actual_effect = reason
        experiment.completed_at = datetime.now(
            timezone.utc
        )

        db.commit()
        db.refresh(experiment)

        return experiment

    def _simulate_failure(
        self,
        experiment: ChaosExperiment,
    ) -> str:
        failure_type = experiment.failure_type
        intensity = experiment.intensity

        effects = {
            "LATENCY_INJECTION": (
                f"Synthetic latency increased by approximately "
                f"{intensity * 100:.0f} ms."
            ),
            "SERVICE_CRASH": (
                "Synthetic service crash condition activated."
            ),
            "DB_SLOWDOWN": (
                f"Synthetic database slowdown activated "
                f"at intensity {intensity:.1f}."
            ),
            "CPU_STRESS": (
                f"Synthetic CPU stress activated "
                f"at intensity {intensity:.1f}."
            ),
            "MEMORY_PRESSURE": (
                f"Synthetic memory pressure activated "
                f"at intensity {intensity:.1f}."
            ),
            "QUEUE_BACKLOG": (
                f"Synthetic queue backlog increased "
                f"to approximately {intensity * 100:.0f} items."
            ),
            "DEPENDENCY_FAILURE": (
                "Synthetic dependency failure condition activated."
            ),
            "BAD_DEPLOYMENT": (
                "Synthetic deployment regression activated."
            ),
        }

        return effects[failure_type]

    def get_experiment(
        self,
        db: Session,
        experiment_id: str,
    ) -> ChaosExperiment | None:
        return (
            db.query(ChaosExperiment)
            .filter(
                ChaosExperiment.experiment_id
                == experiment_id
            )
            .first()
        )


chaos_engine = ChaosEngine()