import pytest

from app.services.anomaly_detector import AnomalyDetector


@pytest.fixture
def detector():
    return AnomalyDetector()


def test_normal_metric_is_not_anomaly(detector):
    result = detector.detect(
        metric_name="payment_latency_ms",
        baseline_value=200,
        observed_value=220,
        threshold_percent=50,
    )

    assert result.is_anomaly is False
    assert result.severity == "INFO"
    assert result.deviation_percent == pytest.approx(10.0)


def test_latency_anomaly_is_detected(detector):
    result = detector.detect(
        metric_name="payment_latency_ms",
        baseline_value=200,
        observed_value=700,
        threshold_percent=50,
    )

    assert result.is_anomaly is True
    assert result.severity == "CRITICAL"
    assert result.deviation_percent == pytest.approx(250.0)


def test_medium_anomaly(detector):
    result = detector.detect(
        metric_name="requests_per_minute",
        baseline_value=100,
        observed_value=180,
        threshold_percent=50,
    )

    assert result.is_anomaly is True
    assert result.severity == "MEDIUM"
    assert result.deviation_percent == pytest.approx(80.0)


def test_decrease_is_detected(detector):
    result = detector.detect(
        metric_name="requests_per_minute",
        baseline_value=1000,
        observed_value=400,
        threshold_percent=50,
    )

    assert result.is_anomaly is True
    assert result.deviation_percent == pytest.approx(60.0)


def test_invalid_baseline_is_rejected(detector):
    with pytest.raises(ValueError):
        detector.detect(
            metric_name="payment_latency_ms",
            baseline_value=0,
            observed_value=100,
            threshold_percent=50,
        )