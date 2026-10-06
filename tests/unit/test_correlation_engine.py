from app.services.correlation_engine import CorrelationEngine
from app.services.timeline_builder import TimelineBuilder


def test_correlation_engine_exists():
    engine = CorrelationEngine()

    assert engine is not None


def test_correlation_engine_has_correlate_method():
    engine = CorrelationEngine()

    assert hasattr(
        engine,
        "correlate_incident",
    )


def test_timeline_builder_exists():
    builder = TimelineBuilder()

    assert builder is not None


def test_timeline_builder_has_build_method():
    builder = TimelineBuilder()

    assert hasattr(
        builder,
        "build",
    )