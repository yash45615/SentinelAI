from app.services.slo_engine import SloEngine


def test_slo_engine_exists():
    engine = SloEngine()

    assert engine is not None


def test_availability_calculation():
    engine = SloEngine()

    result = engine.calculate_availability(
        1000,
        999,
    )

    assert result == 99.9


def test_zero_request_availability():
    engine = SloEngine()

    assert (
        engine.calculate_availability(
            0,
            0,
        )
        == 100.0
    )


def test_error_rate_calculation():
    engine = SloEngine()

    result = engine.calculate_error_rate(
        1000,
        10,
    )

    assert result == 1.0


def test_zero_request_error_rate():
    engine = SloEngine()

    assert (
        engine.calculate_error_rate(
            0,
            0,
        )
        == 0.0
    )


def test_error_budget():
    engine = SloEngine()

    allowed, remaining = (
        engine.calculate_error_budget(
            99.9
        )
    )

    assert allowed == 0.09999999999999432 or abs(
        allowed - 0.1
    ) < 1e-9

    assert abs(
        remaining - 0.0
    ) < 1e-9


def test_burn_rate_healthy():
    engine = SloEngine()

    burn_rate = engine.calculate_burn_rate(
        100.0
    )

    assert burn_rate == 0.0


def test_burn_rate_at_budget():
    engine = SloEngine()

    burn_rate = engine.calculate_burn_rate(
        99.9
    )

    assert abs(
        burn_rate - 1.0
    ) < 1e-9


def test_p95_empty():
    engine = SloEngine()

    assert engine._percentile_95([]) == 0.0


def test_p95_single_value():
    engine = SloEngine()

    assert (
        engine._percentile_95([100.0])
        == 100.0
    )


def test_p95_multiple_values():
    engine = SloEngine()

    result = engine._percentile_95(
        [100, 110, 120, 130, 140]
    )

    assert result >= 100
    assert result <= 140


def test_healthy_status():
    engine = SloEngine()

    result = engine.determine_status(
        True,
        True,
        True,
        True,
        True,
    )

    assert result == "HEALTHY"


def test_breached_status():
    engine = SloEngine()

    result = engine.determine_status(
        False,
        True,
        True,
        True,
        True,
    )

    assert result == "BREACHED"


def test_at_risk_status():
    engine = SloEngine()

    result = engine.determine_status(
        True,
        True,
        True,
        False,
        True,
    )

    assert result == "AT_RISK"


def test_missing_optional_data_status():
    engine = SloEngine()

    result = engine.determine_status(
        True,
        True,
        True,
        None,
        None,
    )

    assert result == "HEALTHY_WITHOUT_FULL_DATA"


def test_invalid_window():
    engine = SloEngine()

    try:
        engine.calculate_service_slo(
            db=None,
            service_id="orders-service",
            window_minutes=0,
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "window_minutes must be greater than zero."
        )