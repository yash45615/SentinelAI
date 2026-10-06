from types import SimpleNamespace

import pytest

from app.services.remediation_engine import (
    ALLOWED_ACTIONS,
    RemediationEngine,
)


def build_incident():
    return SimpleNamespace(
        id=1,
        incident_key="INC-TEST-001",
        service_id="payments-service",
    )


def test_remediation_engine_exists():
    engine = RemediationEngine()

    assert engine is not None


def test_allowed_remediation_actions():
    expected = {
        "RESTART_SERVICE",
        "ROLLBACK_DEPLOYMENT",
        "PAUSE_TRAFFIC",
        "REDUCE_CONCURRENCY",
        "CLEAR_QUEUE",
        "SWITCH_DEPENDENCY",
    }

    assert ALLOWED_ACTIONS == expected


def test_valid_action():
    engine = RemediationEngine()

    valid, message = engine.validate_action(
        action_type="RESTART_SERVICE",
        service_id="payments-service",
    )

    assert valid is True
    assert message == "Action is valid."


def test_invalid_action():
    engine = RemediationEngine()

    valid, message = engine.validate_action(
        action_type="DELETE_DATABASE",
        service_id="payments-service",
    )

    assert valid is False
    assert "Unsupported" in message


def test_missing_service():
    engine = RemediationEngine()

    valid, message = engine.validate_action(
        action_type="RESTART_SERVICE",
        service_id="",
    )

    assert valid is False
    assert "service_id" in message


def test_synthetic_restart():
    engine = RemediationEngine()

    action = SimpleNamespace(
        action_type="RESTART_SERVICE",
        service_id="payments-service",
    )

    result = engine._execute_synthetic_action(
        action
    )

    assert "restart" in result.lower()
    assert "payments-service" in result


def test_synthetic_rollback():
    engine = RemediationEngine()

    action = SimpleNamespace(
        action_type="ROLLBACK_DEPLOYMENT",
        service_id="payments-service",
    )

    result = engine._execute_synthetic_action(
        action
    )

    assert "rollback" in result.lower()


def test_synthetic_queue_clear():
    engine = RemediationEngine()

    action = SimpleNamespace(
        action_type="CLEAR_QUEUE",
        service_id="notifications-service",
    )

    result = engine._execute_synthetic_action(
        action
    )

    assert "queue" in result.lower()


def test_invalid_synthetic_execution():
    engine = RemediationEngine()

    action = SimpleNamespace(
        action_type="UNKNOWN",
        service_id="payments-service",
    )

    with pytest.raises(ValueError):
        engine._execute_synthetic_action(
            action
        )