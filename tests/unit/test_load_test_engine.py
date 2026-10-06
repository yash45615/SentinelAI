from app.services.load_test_engine import (
    LoadTestEngine,
)


def test_load_test_engine_exists():
    engine = LoadTestEngine()

    assert engine is not None


def test_parameter_validation():
    engine = LoadTestEngine()

    engine.validate_parameters(
        concurrency=5,
        duration_seconds=10,
    )


def test_zero_concurrency_rejected():
    engine = LoadTestEngine()

    try:
        engine.validate_parameters(
            concurrency=0,
            duration_seconds=10,
        )
        assert False
    except ValueError:
        assert True


def test_excessive_concurrency_rejected():
    engine = LoadTestEngine()

    try:
        engine.validate_parameters(
            concurrency=101,
            duration_seconds=10,
        )
        assert False
    except ValueError:
        assert True


def test_zero_duration_rejected():
    engine = LoadTestEngine()

    try:
        engine.validate_parameters(
            concurrency=5,
            duration_seconds=0,
        )
        assert False
    except ValueError:
        assert True


def test_excessive_duration_rejected():
    engine = LoadTestEngine()

    try:
        engine.validate_parameters(
            concurrency=5,
            duration_seconds=301,
        )
        assert False
    except ValueError:
        assert True


def test_percentile_empty():
    engine = LoadTestEngine()

    assert (
        engine.percentile([], 95)
        == 0.0
    )


def test_percentile_single():
    engine = LoadTestEngine()

    assert (
        engine.percentile(
            [100.0],
            95,
        )
        == 100.0
    )


def test_percentile_order_independent():
    engine = LoadTestEngine()

    result = engine.percentile(
        [500, 100, 300, 200, 400],
        95,
    )

    assert result >= 400
    assert result <= 500


def test_performance_gate_passes():
    engine = LoadTestEngine()

    status, reason = (
        engine.evaluate_gate(
            p95_latency_ms=200,
            error_rate_percent=0.2,
        )
    )

    assert status == "PASSED"
    assert "passed" in reason.lower()


def test_latency_gate_fails():
    engine = LoadTestEngine()

    status, reason = (
        engine.evaluate_gate(
            p95_latency_ms=600,
            error_rate_percent=0.2,
        )
    )

    assert status == "FAILED"
    assert "latency" in reason.lower()


def test_error_gate_fails():
    engine = LoadTestEngine()

    status, reason = (
        engine.evaluate_gate(
            p95_latency_ms=200,
            error_rate_percent=2.0,
        )
    )

    assert status == "FAILED"
    assert "error rate" in reason.lower()


def test_both_gates_fail():
    engine = LoadTestEngine()

    status, reason = (
        engine.evaluate_gate(
            p95_latency_ms=700,
            error_rate_percent=3.0,
        )
    )

    assert status == "FAILED"
    assert "latency" in reason.lower()
    assert "error rate" in reason.lower()


def test_engine_has_run():
    engine = LoadTestEngine()

    assert hasattr(
        engine,
        "run",
    )


def test_engine_has_gate():
    engine = LoadTestEngine()

    assert hasattr(
        engine,
        "evaluate_gate",
    )