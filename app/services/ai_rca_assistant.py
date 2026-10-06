from dataclasses import dataclass
import json
from typing import Any

import httpx

from app.core.config import settings


@dataclass
class AiRcaResult:
    provider: str
    model: str
    summary: str
    root_cause: str
    reasoning: str
    recommended_action: str
    confidence: float
    selected_hypothesis_id: int | None


class AiRcaAssistant:
    """
    AI-assisted RCA layer.

    Safety design:
    1. Deterministic RCA remains the source of evidence.
    2. AI receives structured evidence.
    3. AI cannot execute remediation.
    4. If AI is unavailable, deterministic fallback is returned.
    """

    def analyze(
        self,
        incident: Any,
        hypotheses: list[Any],
        evidence: list[Any],
    ) -> AiRcaResult:
        if not hypotheses:
            return self._fallback(
                incident=incident,
                hypotheses=[],
                evidence=evidence,
            )

        if not settings.ai_rca_enabled:
            return self._fallback(
                incident=incident,
                hypotheses=hypotheses,
                evidence=evidence,
            )

        if not settings.ai_rca_api_key:
            return self._fallback(
                incident=incident,
                hypotheses=hypotheses,
                evidence=evidence,
            )

        try:
            return self._call_openai(
                incident=incident,
                hypotheses=hypotheses,
                evidence=evidence,
            )
        except Exception:
            return self._fallback(
                incident=incident,
                hypotheses=hypotheses,
                evidence=evidence,
            )

    def _fallback(
        self,
        incident: Any,
        hypotheses: list[Any],
        evidence: list[Any],
    ) -> AiRcaResult:
        top = hypotheses[0] if hypotheses else None

        if top is None:
            return AiRcaResult(
                provider="deterministic",
                model="deterministic-fallback",
                summary=(
                    f"No RCA hypothesis could be generated for incident "
                    f"{incident.incident_key}."
                ),
                root_cause="Unknown",
                reasoning=(
                    "The RCA engine did not produce a candidate hypothesis "
                    "from the available telemetry and evidence."
                ),
                recommended_action=(
                    "Continue evidence collection and investigate the "
                    "affected service manually."
                ),
                confidence=0.0,
                selected_hypothesis_id=None,
            )

        supporting = getattr(
            top,
            "supporting_evidence_count",
            0,
        )

        contradicting = getattr(
            top,
            "contradicting_evidence_count",
            0,
        )

        explanation = getattr(
            top,
            "explanation",
            "",
        )

        confidence = float(
            getattr(
                top,
                "confidence",
                0.0,
            )
        )

        title = getattr(
            top,
            "title",
            "Unknown root cause",
        )

        recommendation = self._recommend_action(
            hypothesis_type=getattr(
                top,
                "hypothesis_type",
                "",
            ),
            service_id=getattr(
                top,
                "service_id",
                incident.service_id,
            ),
        )

        reasoning = (
            f"Deterministic RCA ranked this hypothesis first with "
            f"confidence {confidence:.2f}. "
            f"It has {supporting} supporting evidence items and "
            f"{contradicting} contradicting evidence items. "
            f"{explanation}"
        )

        return AiRcaResult(
            provider="deterministic",
            model="deterministic-fallback",
            summary=(
                f"Most likely root cause for {incident.incident_key}: "
                f"{title}."
            ),
            root_cause=title,
            reasoning=reasoning,
            recommended_action=recommendation,
            confidence=confidence,
            selected_hypothesis_id=getattr(
                top,
                "id",
                None,
            ),
        )

    def _recommend_action(
        self,
        hypothesis_type: str,
        service_id: str,
    ) -> str:
        if hypothesis_type == "DEPENDENCY_FAILURE":
            return (
                f"Inspect dependency health for {service_id}, "
                "verify downstream availability, and prepare a "
                "controlled dependency failover or traffic reduction."
            )

        if hypothesis_type == "INCIDENT_SERVICE_FAILURE":
            return (
                f"Investigate {service_id} health and prepare a "
                "controlled restart or rollback after approval."
            )

        if hypothesis_type == "SERVICE_ANOMALY":
            return (
                f"Inspect recent changes and telemetry for {service_id} "
                "and compare the service against its healthy baseline."
            )

        if hypothesis_type == "POTENTIAL_SERVICE_CAUSE":
            return (
                f"Investigate correlated telemetry for {service_id} "
                "before selecting a remediation action."
            )

        return (
            "Collect additional telemetry and require human approval "
            "before performing remediation."
        )

    def _call_openai(
        self,
        incident: Any,
        hypotheses: list[Any],
        evidence: list[Any],
    ) -> AiRcaResult:
        prompt = self._build_prompt(
            incident=incident,
            hypotheses=hypotheses,
            evidence=evidence,
        )

        payload = {
            "model": settings.ai_rca_model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are SentinelAI's reliability RCA assistant. "
                        "Use only the supplied evidence. "
                        "Do not invent telemetry. "
                        "Do not execute actions. "
                        "Return strict JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

        headers = {
            "Authorization": f"Bearer {settings.ai_rca_api_key}",
            "Content-Type": "application/json",
        }

        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=settings.ai_rca_timeout_seconds,
        )

        response.raise_for_status()

        data = response.json()

        content = data["choices"][0]["message"]["content"]

        parsed = json.loads(content)

        return AiRcaResult(
            provider="openai",
            model=settings.ai_rca_model,
            summary=str(parsed["summary"]),
            root_cause=str(parsed["root_cause"]),
            reasoning=str(parsed["reasoning"]),
            recommended_action=str(
                parsed["recommended_action"]
            ),
            confidence=max(
                0.0,
                min(
                    1.0,
                    float(parsed["confidence"]),
                ),
            ),
            selected_hypothesis_id=(
                int(parsed["selected_hypothesis_id"])
                if parsed.get("selected_hypothesis_id")
                is not None
                else None
            ),
        )

    def _build_prompt(
        self,
        incident: Any,
        hypotheses: list[Any],
        evidence: list[Any],
    ) -> str:
        hypothesis_data = []

        for hypothesis in hypotheses:
            hypothesis_data.append(
                {
                    "id": hypothesis.id,
                    "service_id": hypothesis.service_id,
                    "type": hypothesis.hypothesis_type,
                    "title": hypothesis.title,
                    "explanation": hypothesis.explanation,
                    "confidence": hypothesis.confidence,
                    "anomaly_score": hypothesis.anomaly_score,
                    "temporal_score": hypothesis.temporal_score,
                    "dependency_score": hypothesis.dependency_score,
                    "evidence_score": hypothesis.evidence_score,
                    "log_score": hypothesis.log_score,
                    "trace_score": hypothesis.trace_score,
                }
            )

        evidence_data = []

        for item in evidence:
            evidence_data.append(
                {
                    "type": item.evidence_type,
                    "service_id": item.service_id,
                    "summary": item.summary,
                    "severity": item.severity,
                    "relevance_score": item.relevance_score,
                }
            )

        return json.dumps(
            {
                "incident": {
                    "id": incident.id,
                    "incident_key": incident.incident_key,
                    "title": incident.title,
                    "description": incident.description,
                    "service_id": incident.service_id,
                    "severity": incident.severity,
                    "status": incident.status,
                },
                "hypotheses": hypothesis_data,
                "evidence": evidence_data,
                "required_output": {
                    "selected_hypothesis_id": (
                        "integer or null"
                    ),
                    "summary": "short RCA summary",
                    "root_cause": "most likely root cause",
                    "reasoning": "evidence-based explanation",
                    "recommended_action": (
                        "safe recommended next step"
                    ),
                    "confidence": "number between 0 and 1",
                },
            },
            indent=2,
        )


ai_rca_assistant = AiRcaAssistant()