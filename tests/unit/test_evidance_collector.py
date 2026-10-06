from app.services.evidence_collector import EvidenceCollector


def test_evidence_collector_exists():
    collector = EvidenceCollector()

    assert collector is not None


def test_collector_has_metric_collection():
    collector = EvidenceCollector()

    assert hasattr(
        collector,
        "_collect_metrics",
    )


def test_collector_has_log_collection():
    collector = EvidenceCollector()

    assert hasattr(
        collector,
        "_collect_logs",
    )


def test_collector_has_trace_collection():
    collector = EvidenceCollector()

    assert hasattr(
        collector,
        "_collect_traces",
    )


def test_collector_has_anomaly_collection():
    collector = EvidenceCollector()

    assert hasattr(
        collector,
        "_collect_anomalies",
    )


def test_collector_has_service_collection():
    collector = EvidenceCollector()

    assert hasattr(
        collector,
        "_collect_service",
    )