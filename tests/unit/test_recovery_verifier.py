from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.recovery_verifier import (
    RecoveryCheckResult,
    RecoveryVerifier,
)


def test_recovery_verifier_exists():
    verifier = RecoveryVerifier()

    assert verifier is not None


def test_recovery_verifier_has_service_health_check():
    verifier = RecoveryVerifier()

    assert hasattr(
        verifier,
        "check_service_health",
    )


def test_recovery_verifier_has_latency_check():
    verifier = RecoveryVerifier()

    assert hasattr(
        verifier,
        "check_latency",
    )


def test_recovery_verifier_has_error_rate_check():
    verifier = RecoveryVerifier()

    assert hasattr(
        verifier,
        "check_error_rate",
    )


def test_recovery_verifier_has_dependency_check():
    verifier = RecoveryVerifier()

    assert hasattr(
        verifier,
        "check_dependencies",
    )


def test_recovery_verifier_has_queue_check():
    verifier = RecoveryVerifier()

    assert hasattr(
        verifier,
        "check_queue_backlog",
    )


def test_recovery_verifier_has_run_checks():
    verifier = RecoveryVerifier()

    assert hasattr(
        verifier,
        "run_checks",
    )


def test_recovery_verifier_has_summary():
    verifier = RecoveryVerifier()

    assert hasattr(
        verifier,
        "summarize",
    )


def test_all_passed_summary():
    verifier = RecoveryVerifier()

    results = [
        RecoveryCheckResult(
            check_type="SERVICE_HEALTH",
            service_id="orders-service",
            status="PASSED",
            expected_value=1.0,
            observed_value=1.0,
            details="Healthy",
        ),
        RecoveryCheckResult(
            check_type="LATENCY",
            service_id="orders-service",
            status="PASSED",
            expected_value=500.0,
            observed_value=120.0,
            details="Healthy latency",
        ),
    ]

    assert verifier.summarize(results) == "PASSED"


def test_failed_summary():
    verifier = RecoveryVerifier()

    results = [
        RecoveryCheckResult(
            check_type="SERVICE_HEALTH",
            service_id="orders-service",
            status="PASSED",
            expected_value=1.0,
            observed_value=1.0,
            details="Healthy",
        ),
        RecoveryCheckResult(
            check_type="LATENCY",
            service_id="orders-service",
            status="FAILED",
            expected_value=500.0,
            observed_value=900.0,
            details="Latency still elevated",
        ),
    ]

    assert verifier.summarize(results) == "FAILED"


def test_inconclusive_summary():
    verifier = RecoveryVerifier()

    results = [
        RecoveryCheckResult(
            check_type="LATENCY",
            service_id="orders-service",
            status="INCONCLUSIVE",
            expected_value=500.0,
            observed_value=None,
            details="No telemetry",
        ),
    ]

    assert verifier.summarize(results) == "INCONCLUSIVE"


def test_empty_summary():
    verifier = RecoveryVerifier()

    assert verifier.summarize([]) == "INCONCLUSIVE"


def test_datetime_normalization():
    verifier = RecoveryVerifier()

    naive = datetime(2026, 10, 6, 10, 0, 0)

    normalized = verifier._normalize_datetime(
        naive
    )

    assert normalized.tzinfo == timezone.utc


def test_timezone_datetime_normalization():
    verifier = RecoveryVerifier()

    aware = datetime(
        2026,
        10,
        6,
        10,
        0,
        0,
        tzinfo=timezone.utc,
    )

    normalized = verifier._normalize_datetime(
        aware
    )

    assert normalized.tzinfo == timezone.utc