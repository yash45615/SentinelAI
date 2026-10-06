from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.anomaly import Anomaly
from app.models.incident import Incident
from app.models.incident_evidence import IncidentEvidence
from app.models.log import LogEvent
from app.models.rca_hypothesis import RcaHypothesis
from app.models.trace import TraceSpan
from app.services.correlation_engine import correlation_engine


class RcaEngine:
    """
    Deterministic and explainable Root Cause Analysis engine.

    The engine combines:

    - anomaly strength
    - temporal correlation
    - service dependency correlation
    - incident evidence
    - error logs
    - failed traces

    into a ranked RCA hypothesis list.
    """

    def analyze_incident(
        self,
        db: Session,
        incident: Incident,
    ) -> list[RcaHypothesis]:

        # Make RCA analysis idempotent.
        db.execute(
            delete(RcaHypothesis).where(
                RcaHypothesis.incident_id == incident.id
            )
        )
        db.commit()

        correlations = correlation_engine.correlate_incident(
            db,
            incident,
        )

        incident_time = self._normalize_datetime(
            incident.detected_at
        )

        window_start = incident_time - timedelta(
            minutes=10
        )

        window_end = incident_time + timedelta(
            minutes=10
        )

        candidates: dict[str, dict] = {}

        # --------------------------------------------------------
        # Incident service is always an RCA candidate.
        # --------------------------------------------------------

        self._ensure_candidate(
            candidates,
            incident.service_id,
        )

        # --------------------------------------------------------
        # Add services discovered by correlation.
        # --------------------------------------------------------

        for correlation in correlations:

            self._ensure_candidate(
                candidates,
                correlation.related_service_id,
            )

            candidates[
                correlation.related_service_id
            ]["correlations"].append(
                correlation
            )

        # --------------------------------------------------------
        # Load anomalies.
        # --------------------------------------------------------

        anomaly_statement = (
            select(Anomaly)
            .where(
                Anomaly.detected_at >= window_start,
                Anomaly.detected_at <= window_end,
            )
        )

        anomalies = list(
            db.scalars(
                anomaly_statement
            ).all()
        )

        for anomaly in anomalies:

            if anomaly.service_id not in candidates:
                continue

            candidates[
                anomaly.service_id
            ]["anomalies"].append(
                anomaly
            )

        # --------------------------------------------------------
        # Load incident evidence.
        # --------------------------------------------------------

        evidence_statement = (
            select(IncidentEvidence)
            .where(
                IncidentEvidence.incident_id
                == incident.id
            )
        )

        evidence = list(
            db.scalars(
                evidence_statement
            ).all()
        )

        for item in evidence:

            if item.service_id not in candidates:
                continue

            candidates[
                item.service_id
            ]["evidence"].append(
                item
            )

        # --------------------------------------------------------
        # Load logs.
        # --------------------------------------------------------

        log_statement = (
            select(LogEvent)
            .where(
                LogEvent.timestamp >= window_start,
                LogEvent.timestamp <= window_end,
            )
        )

        logs = list(
            db.scalars(
                log_statement
            ).all()
        )

        for log in logs:

            if log.service_id not in candidates:
                continue

            candidates[
                log.service_id
            ]["logs"].append(
                log
            )

        # --------------------------------------------------------
        # Load traces.
        # --------------------------------------------------------

        trace_statement = (
            select(TraceSpan)
            .where(
                TraceSpan.start_time >= window_start,
                TraceSpan.start_time <= window_end,
            )
        )

        traces = list(
            db.scalars(
                trace_statement
            ).all()
        )

        for trace in traces:

            if trace.service_id not in candidates:
                continue

            candidates[
                trace.service_id
            ]["traces"].append(
                trace
            )

        # --------------------------------------------------------
        # Score candidates.
        # --------------------------------------------------------

        scored_candidates = []

        for service_id, candidate in candidates.items():

            score = self._score_candidate(
                incident=incident,
                service_id=service_id,
                candidate=candidate,
            )

            scored_candidates.append(
                {
                    "service_id": service_id,
                    **score,
                }
            )

        scored_candidates.sort(
            key=lambda item: item["confidence"],
            reverse=True,
        )

        # --------------------------------------------------------
        # Persist hypotheses.
        # --------------------------------------------------------

        hypotheses = []

        for rank, candidate in enumerate(
            scored_candidates,
            start=1,
        ):

            hypothesis = RcaHypothesis(
                incident_id=incident.id,
                service_id=candidate["service_id"],
                hypothesis_type=candidate[
                    "hypothesis_type"
                ],
                title=candidate["title"],
                explanation=candidate["explanation"],
                confidence=candidate["confidence"],

                anomaly_score=candidate[
                    "anomaly_score"
                ],

                temporal_score=candidate[
                    "temporal_score"
                ],

                dependency_score=candidate[
                    "dependency_score"
                ],

                evidence_score=candidate[
                    "evidence_score"
                ],

                log_score=candidate[
                    "log_score"
                ],

                trace_score=candidate[
                    "trace_score"
                ],

                supporting_evidence_count=candidate[
                    "supporting_evidence_count"
                ],

                contradicting_evidence_count=candidate[
                    "contradicting_evidence_count"
                ],

                rank=rank,
            )

            db.add(hypothesis)

            hypotheses.append(
                hypothesis
            )

        db.commit()

        for hypothesis in hypotheses:
            db.refresh(hypothesis)

        return hypotheses

    # ============================================================
    # Candidate Management
    # ============================================================

    @staticmethod
    def _ensure_candidate(
        candidates: dict,
        service_id: str,
    ):

        if service_id not in candidates:

            candidates[service_id] = {
                "anomalies": [],
                "evidence": [],
                "logs": [],
                "traces": [],
                "correlations": [],
            }

    # ============================================================
    # Candidate Scoring
    # ============================================================

    def _score_candidate(
        self,
        incident: Incident,
        service_id: str,
        candidate: dict,
    ) -> dict:

        incident_time = self._normalize_datetime(
            incident.detected_at
        )

        anomalies = candidate["anomalies"]
        evidence = candidate["evidence"]
        logs = candidate["logs"]
        traces = candidate["traces"]
        correlations = candidate["correlations"]

        # --------------------------------------------------------
        # 1. Anomaly strength
        # --------------------------------------------------------

        anomaly_score = 0.0
        strongest_anomaly = None

        if anomalies:

            strongest_anomaly = max(
                anomalies,
                key=lambda anomaly:
                    anomaly.deviation_percent,
            )

            deviation = max(
                strongest_anomaly.deviation_percent,
                0.0,
            )

            anomaly_score = min(
                deviation / 500.0,
                1.0,
            )

        # --------------------------------------------------------
        # 2. Temporal correlation
        # --------------------------------------------------------

        temporal_score = 0.0

        if strongest_anomaly:

            anomaly_time = self._normalize_datetime(
                strongest_anomaly.detected_at
            )

            gap = (
                incident_time - anomaly_time
            ).total_seconds()

            if gap >= 0:

                temporal_score = max(
                    0.0,
                    1.0 - (
                        gap / 300.0
                    ),
                )

            else:

                temporal_score = max(
                    0.0,
                    0.5 - (
                        abs(gap) / 600.0
                    ),
                )

        # --------------------------------------------------------
        # 3. Dependency correlation
        # --------------------------------------------------------

        dependency_score = 0.0
        strongest_correlation = None

        if correlations:

            strongest_correlation = max(
                correlations,
                key=lambda correlation:
                    correlation.correlation_score,
            )

            dependency_score = min(
                max(
                    strongest_correlation.correlation_score,
                    0.0,
                ),
                1.0,
            )

        # --------------------------------------------------------
        # 4. Evidence score
        # --------------------------------------------------------

        evidence_score = 0.0

        if evidence:

            relevance_values = [
                max(
                    min(
                        float(
                            item.relevance_score
                        ),
                        1.0,
                    ),
                    0.0,
                )
                for item in evidence
            ]

            if relevance_values:

                evidence_score = min(
                    sum(
                        relevance_values
                    ) / len(
                        relevance_values
                    ),
                    1.0,
                )

        # --------------------------------------------------------
        # 5. Log score
        # --------------------------------------------------------

        error_log_count = sum(
            1
            for log in logs
            if str(
                log.level
            ).upper()
            in {
                "ERROR",
                "CRITICAL",
            }
        )

        log_score = min(
            error_log_count / 5.0,
            1.0,
        )

        # --------------------------------------------------------
        # 6. Trace score
        # --------------------------------------------------------

        failed_trace_count = sum(
            1
            for trace in traces
            if str(
                trace.status
            ).upper()
            in {
                "ERROR",
                "FAILED",
            }
        )

        trace_score = min(
            failed_trace_count / 5.0,
            1.0,
        )

        # --------------------------------------------------------
        # Weighted confidence
        # --------------------------------------------------------

        confidence = (
            anomaly_score * 0.30
            + temporal_score * 0.20
            + dependency_score * 0.20
            + evidence_score * 0.15
            + log_score * 0.10
            + trace_score * 0.05
        )

        confidence = round(
            min(
                max(
                    confidence,
                    0.0,
                ),
                1.0,
            ),
            4,
        )

        # --------------------------------------------------------
        # Evidence counts
        # --------------------------------------------------------

        supporting_evidence_count = (
            len(anomalies)
            + len(evidence)
            + error_log_count
            + failed_trace_count
            + len(correlations)
        )

        contradicting_evidence_count = 0

        if strongest_anomaly:

            anomaly_time = self._normalize_datetime(
                strongest_anomaly.detected_at
            )

            if anomaly_time > incident_time:
                contradicting_evidence_count += 1

        # --------------------------------------------------------
        # Hypothesis type
        # --------------------------------------------------------

        if service_id == incident.service_id:

            hypothesis_type = (
                "INCIDENT_SERVICE_FAILURE"
            )

            title = (
                f"{service_id} directly degraded"
            )

        elif correlations:

            hypothesis_type = (
                "DEPENDENCY_FAILURE"
            )

            title = (
                f"{service_id} dependency degradation"
            )

        elif anomalies:

            hypothesis_type = (
                "SERVICE_ANOMALY"
            )

            title = (
                f"{service_id} anomalous behavior"
            )

        else:

            hypothesis_type = (
                "POTENTIAL_SERVICE_CAUSE"
            )

            title = (
                f"{service_id} potential root cause"
            )

        # --------------------------------------------------------
        # Explanation
        # --------------------------------------------------------

        explanation_parts = []

        if strongest_anomaly:

            explanation_parts.append(
                f"{strongest_anomaly.metric_name} "
                f"deviated by "
                f"{strongest_anomaly.deviation_percent:.2f}% "
                f"from its baseline."
            )

        if strongest_correlation:

            explanation_parts.append(
                "The service has a correlated "
                "dependency relationship with "
                "the incident."
            )

            if (
                strongest_correlation
                .temporal_gap_seconds >= 0
            ):

                explanation_parts.append(
                    "The related anomaly occurred "
                    "before the incident."
                )

        if error_log_count:

            explanation_parts.append(
                f"{error_log_count} error-level "
                "log event(s) were observed."
            )

        if failed_trace_count:

            explanation_parts.append(
                f"{failed_trace_count} failed "
                "trace span(s) were observed."
            )

        if evidence:

            explanation_parts.append(
                f"{len(evidence)} incident evidence "
                "item(s) support this candidate."
            )

        if not explanation_parts:

            explanation_parts.append(
                "Insufficient direct evidence was "
                "available; this service remains "
                "a candidate based on incident topology."
            )

        # --------------------------------------------------------
        # Explainable scoring
        # --------------------------------------------------------

        score_explanation = (
            f"Scoring breakdown: "
            f"anomaly={anomaly_score:.2f}, "
            f"temporal={temporal_score:.2f}, "
            f"dependency={dependency_score:.2f}, "
            f"evidence={evidence_score:.2f}, "
            f"logs={log_score:.2f}, "
            f"traces={trace_score:.2f}."
        )

        explanation_parts.append(
            score_explanation
        )

        explanation = " ".join(
            explanation_parts
        )

        return {
            "hypothesis_type": hypothesis_type,
            "title": title,
            "explanation": explanation,
            "confidence": confidence,

            "anomaly_score": round(
                anomaly_score,
                4,
            ),

            "temporal_score": round(
                temporal_score,
                4,
            ),

            "dependency_score": round(
                dependency_score,
                4,
            ),

            "evidence_score": round(
                evidence_score,
                4,
            ),

            "log_score": round(
                log_score,
                4,
            ),

            "trace_score": round(
                trace_score,
                4,
            ),

            "supporting_evidence_count": (
                supporting_evidence_count
            ),

            "contradicting_evidence_count": (
                contradicting_evidence_count
            ),
        }

    # ============================================================
    # Datetime Helper
    # ============================================================

    @staticmethod
    def _normalize_datetime(
        value: datetime,
    ) -> datetime:

        if value.tzinfo is None:

            return value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(
            timezone.utc
        )


rca_engine = RcaEngine()