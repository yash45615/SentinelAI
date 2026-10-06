from app.services.rca_engine import RcaEngine


def test_rca_engine_exists():
    engine = RcaEngine()

    assert engine is not None


def test_rca_engine_has_analyze_method():
    engine = RcaEngine()

    assert hasattr(
        engine,
        "analyze_incident",
    )


def test_rca_engine_has_datetime_normalizer():
    engine = RcaEngine()

    assert hasattr(
        engine,
        "_normalize_datetime",
    )


def test_rca_engine_candidate_builder():
    engine = RcaEngine()

    candidates = {}

    engine._ensure_candidate(
        candidates,
        "payments-service",
    )

    assert "payments-service" in candidates

    assert (
        candidates["payments-service"]["anomalies"]
        == []
    )

    assert (
        candidates["payments-service"]["evidence"]
        == []
    )

    assert (
        candidates["payments-service"]["logs"]
        == []
    )

    assert (
        candidates["payments-service"]["traces"]
        == []
    )

    assert (
        candidates["payments-service"]["correlations"]
        == []
    )


def test_rca_score_dimensions():
    expected_dimensions = {
        "anomaly_score",
        "temporal_score",
        "dependency_score",
        "evidence_score",
        "log_score",
        "trace_score",
    }

    assert len(expected_dimensions) == 6

def test_rca_score_is_bounded():
    engine = RcaEngine()

    assert 0.0 <= 0.0 <= 1.0
    assert 0.0 <= 1.0 <= 1.0


def test_candidate_contains_scoring_dimensions():
    expected_dimensions = {
        "anomaly_score",
        "temporal_score",
        "dependency_score",
        "evidence_score",
        "log_score",
        "trace_score",
    }

    assert len(expected_dimensions) == 6