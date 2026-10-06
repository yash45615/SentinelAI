from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.anomaly import Anomaly
from app.models.incident import Incident
from app.models.incident_evidence import IncidentEvidence
from app.models.log import LogEvent
from app.models.metric import MetricSample
from app.models.service import Service
from app.models.trace import TraceSpan


class EvidenceCollector:

    def collect(
        self,
        db: Session,
        incident: Incident,
        before_minutes: int = 5,
        after_minutes: int = 5,
    ) -> list[IncidentEvidence]:

        incident_time = incident.detected_at

        if incident_time.tzinfo is None:
            incident_time = incident_time.replace(
                tzinfo=timezone.utc
            )

        start_time = incident_time - timedelta(
            minutes=before_minutes
        )

        end_time = incident_time + timedelta(
            minutes=after_minutes
        )

        evidence: list[IncidentEvidence] = []

        self._collect_metrics(
            db,
            incident,
            start_time,
            end_time,
            evidence,
        )

        self._collect_logs(
            db,
            incident,
            start_time,
            end_time,
            evidence,
        )

        self._collect_traces(
            db,
            incident,
            start_time,
            end_time,
            evidence,
        )

        self._collect_anomalies(
            db,
            incident,
            start_time,
            end_time,
            evidence,
        )

        self._collect_service(
            db,
            incident,
            evidence,
        )

        for item in evidence:
            db.add(item)

        db.commit()

        return evidence

    def _collect_metrics(
        self,
        db: Session,
        incident: Incident,
        start_time: datetime,
        end_time: datetime,
        evidence: list[IncidentEvidence],
    ):

        statement = (
            select(MetricSample)
            .where(
                MetricSample.service_id == incident.service_id,
                MetricSample.timestamp >= start_time,
                MetricSample.timestamp <= end_time,
            )
            .order_by(MetricSample.timestamp.asc())
        )

        metrics = list(db.scalars(statement).all())

        for metric in metrics:
            evidence.append(
                IncidentEvidence(
                    incident_id=incident.id,
                    evidence_type="METRIC",
                    source_id=str(metric.id),
                    service_id=metric.service_id,
                    summary=(
                        f"Metric {metric.metric_name} recorded "
                        f"value {metric.value} {metric.unit or ''}."
                    ),
                    severity=(
                        "HIGH"
                        if metric.metric_name in {
                            "error_rate_percent",
                            "payment_error_rate",
                        }
                        and metric.value > 5
                        else "INFO"
                    ),
                    relevance_score=0.70,
                    evidence_timestamp=metric.timestamp,
                    collected_at=datetime.now(timezone.utc),
                )
            )

    def _collect_logs(
        self,
        db: Session,
        incident: Incident,
        start_time: datetime,
        end_time: datetime,
        evidence: list[IncidentEvidence],
    ):

        statement = (
            select(LogEvent)
            .where(
                LogEvent.service_id == incident.service_id,
                LogEvent.timestamp >= start_time,
                LogEvent.timestamp <= end_time,
            )
            .order_by(LogEvent.timestamp.asc())
        )

        logs = list(db.scalars(statement).all())

        for log in logs:
            severity = log.level.upper()

            if severity == "ERROR":
                relevance = 0.95
            elif severity == "WARNING":
                relevance = 0.75
            else:
                relevance = 0.40

            evidence.append(
                IncidentEvidence(
                    incident_id=incident.id,
                    evidence_type="LOG",
                    source_id=str(log.id),
                    service_id=log.service_id,
                    summary=(
                        f"{log.level} log: {log.message}"
                    ),
                    severity=severity,
                    relevance_score=relevance,
                    evidence_timestamp=log.timestamp,
                    collected_at=datetime.now(timezone.utc),
                )
            )

    def _collect_traces(
        self,
        db: Session,
        incident: Incident,
        start_time: datetime,
        end_time: datetime,
        evidence: list[IncidentEvidence],
    ):

        statement = (
            select(TraceSpan)
            .where(
                TraceSpan.service_id == incident.service_id,
                TraceSpan.start_time >= start_time,
                TraceSpan.start_time <= end_time,
            )
            .order_by(TraceSpan.start_time.asc())
        )

        traces = list(db.scalars(statement).all())

        for trace in traces:
            severity = (
                "HIGH"
                if trace.status.upper() == "ERROR"
                else "INFO"
            )

            relevance = (
                0.90
                if trace.status.upper() == "ERROR"
                else 0.50
            )

            evidence.append(
                IncidentEvidence(
                    incident_id=incident.id,
                    evidence_type="TRACE",
                    source_id=trace.span_id,
                    service_id=trace.service_id,
                    summary=(
                        f"Trace operation {trace.operation} "
                        f"completed in {trace.duration_ms} ms "
                        f"with status {trace.status}."
                    ),
                    severity=severity,
                    relevance_score=relevance,
                    evidence_timestamp=trace.start_time,
                    collected_at=datetime.now(timezone.utc),
                )
            )

    def _collect_anomalies(
        self,
        db: Session,
        incident: Incident,
        start_time: datetime,
        end_time: datetime,
        evidence: list[IncidentEvidence],
    ):

        statement = (
            select(Anomaly)
            .where(
                Anomaly.service_id == incident.service_id,
                Anomaly.detected_at >= start_time,
                Anomaly.detected_at <= end_time,
            )
            .order_by(Anomaly.detected_at.asc())
        )

        anomalies = list(db.scalars(statement).all())

        for anomaly in anomalies:
            severity = anomaly.severity.upper()

            relevance_map = {
                "CRITICAL": 1.0,
                "HIGH": 0.95,
                "MEDIUM": 0.80,
                "LOW": 0.60,
                "INFO": 0.30,
            }

            evidence.append(
                IncidentEvidence(
                    incident_id=incident.id,
                    evidence_type="ANOMALY",
                    source_id=str(anomaly.id),
                    service_id=anomaly.service_id,
                    summary=(
                        f"{anomaly.metric_name} deviated "
                        f"{anomaly.deviation_percent:.2f}% "
                        f"from baseline."
                    ),
                    severity=severity,
                    relevance_score=relevance_map.get(
                        severity,
                        0.50,
                    ),
                    evidence_timestamp=anomaly.detected_at,
                    collected_at=datetime.now(timezone.utc),
                )
            )

    def _collect_service(
        self,
        db: Session,
        incident: Incident,
        evidence: list[IncidentEvidence],
    ):

        statement = select(Service).where(
            Service.service_id == incident.service_id
        )

        service = db.scalar(statement)

        if service is None:
            return

        evidence.append(
            IncidentEvidence(
                incident_id=incident.id,
                evidence_type="SERVICE",
                source_id=str(service.id),
                service_id=service.service_id,
                summary=(
                    f"Service {service.service_id} "
                    f"is registered in environment "
                    f"{service.environment}."
                ),
                severity="INFO",
                relevance_score=0.50,
                evidence_timestamp=incident.detected_at,
                collected_at=datetime.now(timezone.utc),
            )
        )


evidence_collector = EvidenceCollector()