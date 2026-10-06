from types import SimpleNamespace

from app.services.ai_rca_assistant import AiRcaAssistant


def build_incident():
    return SimpleNamespace(
        id=1,
        incident_key="INC-TEST-001",
        title="Payment latency incident",
        description="Payment requests are slow.",
        service_id="payments-service",
        severity="HIGH",
        status="INVESTIGATING",
    )


def build_hypothesis():
    return SimpleNamespace(
        id=10,
        service_id="payments-service",
        hypothesis_type="INCIDENT_SERVICE_FAILURE",
        title="Payment Service failure",
        explanation=(
            "Payment Service shows a strong anomaly "
            "correlated with the incident."
        ),
        confidence=0.82,
        anomaly_score=0.90,
        temporal_score=0.85,
        dependency_score=0.70,
        evidence_score=0.80,
        log_score=0.60,
        trace_score=0.50,
        supporting_evidence_count=5,
        contradicting_evidence_count=1,
    )


def build_evidence():
    return [
        SimpleNamespace(
            evidence_type="ANOMALY",
            service_id="payments-service",
            summary="Payment latency increased sharply.",
            severity="HIGH",
            relevance_score=0.95,
        )
    ]


def test_ai_rca_assistant_exists():
    assistant = AiRcaAssistant()

    assert assistant is not None


def test_ai_rca_has_analyze_method():
    assistant = AiRcaAssistant()

    assert hasattr(
        assistant,
        "analyze",
    )


def test_ai_rca_fallback_produces_result():
    assistant = AiRcaAssistant()

    result = assistant.analyze(
        incident=build_incident(),
        hypotheses=[build_hypothesis()],
        evidence=build_evidence(),
    )

    assert result is not None
    assert result.provider == "deterministic"
    assert result.model == "deterministic-fallback"
    assert result.selected_hypothesis_id == 10
    assert result.confidence == 0.82


def test_ai_rca_fallback_contains_reasoning():
    assistant = AiRcaAssistant()

    result = assistant.analyze(
        incident=build_incident(),
        hypotheses=[build_hypothesis()],
        evidence=build_evidence(),
    )

    assert "Deterministic RCA" in result.reasoning
    assert "supporting evidence" in result.reasoning


def test_ai_rca_recommends_safe_action():
    assistant = AiRcaAssistant()

    result = assistant.analyze(
        incident=build_incident(),
        hypotheses=[build_hypothesis()],
        evidence=build_evidence(),
    )

    assert "approval" in result.recommended_action.lower()


def test_ai_rca_handles_no_hypotheses():
    assistant = AiRcaAssistant()

    result = assistant.analyze(
        incident=build_incident(),
        hypotheses=[],
        evidence=[],
    )

    assert result.confidence == 0.0
    assert result.selected_hypothesis_id is None
    assert result.root_cause == "Unknown"