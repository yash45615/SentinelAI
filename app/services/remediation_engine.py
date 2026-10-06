from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.remediation_action import RemediationAction


ALLOWED_ACTIONS = {
    "RESTART_SERVICE",
    "ROLLBACK_DEPLOYMENT",
    "PAUSE_TRAFFIC",
    "REDUCE_CONCURRENCY",
    "CLEAR_QUEUE",
    "SWITCH_DEPENDENCY",
}


@dataclass
class RemediationResult:
    action_id: int
    status: str
    result: str


class RemediationEngine:

    def validate_action(
        self,
        action_type: str,
        service_id: str,
    ) -> tuple[bool, str]:
        if action_type not in ALLOWED_ACTIONS:
            return (
                False,
                f"Unsupported remediation action: {action_type}",
            )

        if not service_id:
            return (
                False,
                "service_id is required.",
            )

        return True, "Action is valid."

    def create_action(
        self,
        db: Session,
        incident: Any,
        service_id: str,
        action_type: str,
        reason: str,
    ) -> RemediationAction:

        valid, message = self.validate_action(
            action_type=action_type,
            service_id=service_id,
        )

        if not valid:
            raise ValueError(message)

        action = RemediationAction(
            incident_id=incident.id,
            service_id=service_id,
            action_type=action_type,
            reason=reason,
            status="PENDING",
            rollback_available=True,
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        return action

    def execute_action(
        self,
        db: Session,
        action: RemediationAction,
    ) -> RemediationResult:

        if action.status != "PENDING":
            raise ValueError(
                f"Action cannot be executed from status "
                f"{action.status}."
            )

        action.status = "EXECUTING"
        action.started_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(action)

        try:
            result = self._execute_synthetic_action(
                action=action,
            )

            action.status = "COMPLETED"
            action.result = result
            action.completed_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(action)

            return RemediationResult(
                action_id=action.id,
                status=action.status,
                result=result,
            )

        except Exception as exc:
            action.status = "FAILED"
            action.result = str(exc)
            action.completed_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(action)

            return RemediationResult(
                action_id=action.id,
                status=action.status,
                result=str(exc),
            )

    def _execute_synthetic_action(
        self,
        action: RemediationAction,
    ) -> str:

        if action.action_type == "RESTART_SERVICE":
            return (
                f"Synthetic restart executed for "
                f"{action.service_id}."
            )

        if action.action_type == "ROLLBACK_DEPLOYMENT":
            return (
                f"Synthetic deployment rollback executed for "
                f"{action.service_id}."
            )

        if action.action_type == "PAUSE_TRAFFIC":
            return (
                f"Synthetic traffic pause executed for "
                f"{action.service_id}."
            )

        if action.action_type == "REDUCE_CONCURRENCY":
            return (
                f"Synthetic concurrency reduction executed for "
                f"{action.service_id}."
            )

        if action.action_type == "CLEAR_QUEUE":
            return (
                f"Synthetic queue clearing executed for "
                f"{action.service_id}."
            )

        if action.action_type == "SWITCH_DEPENDENCY":
            return (
                f"Synthetic dependency switch executed for "
                f"{action.service_id}."
            )

        raise ValueError(
            f"Unsupported remediation action: "
            f"{action.action_type}"
        )


remediation_engine = RemediationEngine()