from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.services.approval_gateway import (
    ApprovalGateway,
)


def build_incident():
    return SimpleNamespace(
        id=1,
        incident_key="INC-TEST-001",
    )


def build_action():
    return SimpleNamespace(
        id=10,
        incident_id=1,
        action_type="RESTART_SERVICE",
        status="PENDING",
        reason="Payment service is unhealthy.",
    )


def build_approval(
    status="PENDING",
    valid=True,
    expires_in_minutes=15,
):
    return SimpleNamespace(
        id=100,
        remediation_action_id=10,
        incident_id=1,
        status=status,
        is_valid=valid,
        expires_at=(
            datetime.now(timezone.utc)
            + timedelta(
                minutes=expires_in_minutes
            )
        ),
    )


def test_approval_gateway_exists():
    gateway = ApprovalGateway()

    assert gateway is not None


def test_valid_approval_request():
    gateway = ApprovalGateway()

    valid, message = gateway.validate_request(
        action=build_action(),
        incident=build_incident(),
    )

    assert valid is True
    assert message == "Approval request is valid."


def test_wrong_incident_rejected():
    gateway = ApprovalGateway()

    action = build_action()
    action.incident_id = 999

    valid, message = gateway.validate_request(
        action=action,
        incident=build_incident(),
    )

    assert valid is False
    assert "does not belong" in message


def test_non_pending_action_rejected():
    gateway = ApprovalGateway()

    action = build_action()
    action.status = "COMPLETED"

    valid, message = gateway.validate_request(
        action=action,
        incident=build_incident(),
    )

    assert valid is False
    assert "PENDING" in message


def test_invalid_action_rejected():
    gateway = ApprovalGateway()

    action = build_action()
    action.action_type = "DELETE_DATABASE"

    valid, message = gateway.validate_request(
        action=action,
        incident=build_incident(),
    )

    assert valid is False
    assert "Unsupported" in message


def test_execution_requires_approval():
    gateway = ApprovalGateway()

    valid, message = gateway.authorize_execution(
        approval=build_approval(
            status="PENDING"
        ),
        action=build_action(),
    )

    assert valid is False
    assert "APPROVED" in message


def test_rejected_approval_cannot_execute():
    gateway = ApprovalGateway()

    valid, message = gateway.authorize_execution(
        approval=build_approval(
            status="REJECTED",
            valid=False,
        ),
        action=build_action(),
    )

    assert valid is False
    assert "APPROVED" in message


def test_expired_approval_cannot_execute():
    gateway = ApprovalGateway()

    approval = build_approval(
        status="APPROVED",
        valid=True,
        expires_in_minutes=-1,
    )

    valid, message = gateway.authorize_execution(
        approval=approval,
        action=build_action(),
    )

    assert valid is False
    assert "expired" in message.lower()


def test_valid_approved_action_can_execute():
    gateway = ApprovalGateway()

    valid, message = gateway.authorize_execution(
        approval=build_approval(
            status="APPROVED",
            valid=True,
        ),
        action=build_action(),
    )

    assert valid is True
    assert message == "Execution authorized."


def test_approved_action_must_still_be_pending():
    gateway = ApprovalGateway()

    action = build_action()
    action.status = "COMPLETED"

    valid, message = gateway.authorize_execution(
        approval=build_approval(
            status="APPROVED",
            valid=True,
        ),
        action=action,
    )

    assert valid is False
    assert "not executable" in message