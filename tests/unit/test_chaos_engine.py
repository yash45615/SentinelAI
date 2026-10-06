import pytest

from app.services.chaos_engine import (
    ChaosEngine,
    ChaosValidationError,
)


def test_chaos_engine_exists():
    engine = ChaosEngine()

    assert engine is not None


def test_allowed_failure_types():
    engine = ChaosEngine()

    expected = {
        "LATENCY_INJECTION",
        "SERVICE_CRASH",
        "DB_SLOWDOWN",
        "CPU_STRESS",
        "MEMORY_PRESSURE",
        "QUEUE_BACKLOG",
        "DEPENDENCY_FAILURE",
        "BAD_DEPLOYMENT",
    }

    assert engine.ALLOWED_FAILURE_TYPES == expected


def test_valid_failure_type():
    engine = ChaosEngine()

    result = engine.validate_failure_type(
        "latency_injection"
    )

    assert result == "LATENCY_INJECTION"


def test_invalid_failure_type():
    engine = ChaosEngine()

    with pytest.raises(ChaosValidationError):
        engine.validate_failure_type(
            "DELETE_DATABASE"
        )


def test_intensity_validation():
    engine = ChaosEngine()

    assert engine.validate_intensity(5) == 5.0


def test_zero_intensity_rejected():
    engine = ChaosEngine()

    with pytest.raises(ChaosValidationError):
        engine.validate_intensity(0)


def test_excessive_intensity_rejected():
    engine = ChaosEngine()

    with pytest.raises(ChaosValidationError):
        engine.validate_intensity(11)


def test_duration_validation():
    engine = ChaosEngine()

    assert engine.validate_duration(30) == 30


def test_zero_duration_rejected():
    engine = ChaosEngine()

    with pytest.raises(ChaosValidationError):
        engine.validate_duration(0)


def test_excessive_duration_rejected():
    engine = ChaosEngine()

    with pytest.raises(ChaosValidationError):
        engine.validate_duration(301)


def test_expected_effect_exists_for_every_failure():
    engine = ChaosEngine()

    for failure_type in engine.ALLOWED_FAILURE_TYPES:
        assert failure_type in engine.EXPECTED_EFFECTS
        assert engine.EXPECTED_EFFECTS[failure_type]


def test_engine_has_create_experiment():
    engine = ChaosEngine()

    assert hasattr(
        engine,
        "create_experiment",
    )


def test_engine_has_start_experiment():
    engine = ChaosEngine()

    assert hasattr(
        engine,
        "start_experiment",
    )


def test_engine_has_complete_experiment():
    engine = ChaosEngine()

    assert hasattr(
        engine,
        "complete_experiment",
    )


def test_engine_has_fail_experiment():
    engine = ChaosEngine()

    assert hasattr(
        engine,
        "fail_experiment",
    )


def test_engine_has_failure_simulation():
    engine = ChaosEngine()

    assert hasattr(
        engine,
        "_simulate_failure",
    )