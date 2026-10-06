from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.remediation_action import RemediationAction
from app.models.remediation_approval import RemediationApproval
from app.services.remediation_engine import ALLOWED_ACTIONS


APPROVAL_TTL_MINUTES = 15


class ApprovalGateway:

    def validate_request(
        self,
        action: RemediationAction,
        incident: Any,
    ) -> tuple[bool, str]:
        if action.incident_id != incident.id:
            return (
                False,
                "Remediation action does not belong to this incident.",
            )

        if action.action_type not in ALLOWED_ACTIONS:
            return (
                False,
                f"Unsupported remediation action: "
                f"{action.action_type}",
            )

        if action.status != "PENDING":
            return (
                False,
                f"Remediation action must be PENDING. "
                f"Current status: {action.status}.",
            )

        return True, "Approval request is valid."

    def request_approval(
        self,
        db: Session,
        incident: Any,
        action: RemediationAction,
        requested_by: str = "sentinelai",
    ) -> RemediationApproval:
        valid, message = self.validate_request(
            action=action,
            incident=incident,
        )

        if not valid:
            raise ValueError(message)

        existing = (
            db.query(RemediationApproval)
            .filter(
                RemediationApproval.remediation_action_id
                == action.id
            )
            .filter(
                RemediationApproval.status == "PENDING"
            )
            .first()
        )

        if existing is not None:
            raise ValueError(
                "A pending approval already exists for this action."
            )

        now = datetime.now(timezone.utc)

        approval = RemediationApproval(
            remediation_action_id=action.id,
            incident_id=incident.id,
            requested_by=requested_by,
            status="PENDING",
            reason=action.reason,
            expires_at=(
                now
                + timedelta(
                    minutes=APPROVAL_TTL_MINUTES
                )
            ),
            created_at=now,
            is_valid=True,
        )

        db.add(approval)
        db.commit()
        db.refresh(approval)

        return approval

    def approve(
        self,
        db: Session,
        approval: RemediationApproval,
        approved_by: str,
        decision_reason: str,
    ) -> RemediationApproval:
        self._ensure_decidable(approval)

        if not approved_by:
            raise ValueError(
                "approved_by is required."
            )

        approval.status = "APPROVED"
        approval.approved_by = approved_by
        approval.decision_reason = decision_reason
        approval.decided_at = datetime.now(timezone.utc)
        approval.is_valid = True

        db.commit()
        db.refresh(approval)

        return approval

    def reject(
        self,
        db: Session,
        approval: RemediationApproval,
        rejected_by: str,
        decision_reason: str,
    ) -> RemediationApproval:
        self._ensure_decidable(approval)

        if not rejected_by:
            raise ValueError(
                "rejected_by is required."
            )

        approval.status = "REJECTED"
        approval.approved_by = rejected_by
        approval.decision_reason = decision_reason
        approval.decided_at = datetime.now(timezone.utc)
        approval.is_valid = False

        db.commit()
        db.refresh(approval)

        return approval

    def authorize_execution(
        self,
        approval: RemediationApproval,
        action: RemediationAction,
    ) -> tuple[bool, str]:
        if approval.remediation_action_id != action.id:
            return (
                False,
                "Approval does not belong to remediation action.",
            )

        if approval.status != "APPROVED":
            return (
                False,
                f"Execution requires APPROVED status. "
                f"Current status: {approval.status}.",
            )

        if not approval.is_valid:
            return (
                False,
                "Approval is no longer valid.",
            )

        now = datetime.now(timezone.utc)

        expires_at = approval.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if now >= expires_at:
            return (
                False,
                "Approval has expired.",
            )

        if action.status != "PENDING":
            return (
                False,
                f"Remediation action is not executable. "
                f"Current status: {action.status}.",
            )

        return True, "Execution authorized."

    def _ensure_decidable(
        self,
        approval: RemediationApproval,
    ) -> None:
        if approval.status != "PENDING":
            raise ValueError(
                f"Approval cannot be decided from status "
                f"{approval.status}."
            )

        now = datetime.now(timezone.utc)

        expires_at = approval.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if now >= expires_at:
            approval.status = "EXPIRED"
            approval.is_valid = False

            raise ValueError(
                "Approval has expired."
            )


approval_gateway = ApprovalGateway()