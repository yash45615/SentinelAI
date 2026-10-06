from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.anomaly import Anomaly
from app.models.dependency import ServiceDependency
from app.models.incident import Incident
from app.models.incident_evidence import IncidentEvidence


class CorrelationEngine:

    def correlate_incident(
        self,
        db: Session,
        incident: Incident,
    ) -> list[dict]:

        results = []

        dependencies = list(
            db.scalars(
                select(ServiceDependency).where(
                    ServiceDependency.active.is_(True),
                    (
                        (ServiceDependency.source_service_id == incident.service_id)
                        | (
                            ServiceDependency.target_service_id
                            == incident.service_id
                        )
                    ),
                )
            ).all()
        )

        for dependency in dependencies:

            if (
                dependency.source_service_id
                == incident.service_id
            ):
                related_service = (
                    dependency.target_service_id
                )
                relationship = "DOWNSTREAM"
            else:
                related_service = (
                    dependency.source_service_id
                )
                relationship = "UPSTREAM"

            related_anomalies = list(
                db.scalars(
                    select(Anomaly).where(
                        Anomaly.service_id
                        == related_service
                    )
                ).all()
            )

            temporal_gap = None
            evidence_count = 0

            incident_time = incident.detected_at

            if incident_time.tzinfo is None:
                incident_time = incident_time.replace(
                    tzinfo=timezone.utc
                )

            for anomaly in related_anomalies:

                anomaly_time = anomaly.detected_at

                if anomaly_time.tzinfo is None:
                    anomaly_time = anomaly_time.replace(
                        tzinfo=timezone.utc
                    )

                gap = (
                    incident_time - anomaly_time
                ).total_seconds()

                if abs(gap) <= 300:

                    evidence_count += 1

                    if (
                        temporal_gap is None
                        or abs(gap)
                        < abs(temporal_gap)
                    ):
                        temporal_gap = gap

            if temporal_gap is None:
                continue

            temporal_score = max(
                0.0,
                1.0 - abs(temporal_gap) / 300.0,
            )

            dependency_score = {
                "CRITICAL": 1.0,
                "HIGH": 0.9,
                "MEDIUM": 0.7,
                "LOW": 0.5,
            }.get(
                dependency.criticality.upper(),
                0.5,
            )

            correlation_score = (
                temporal_score * 0.6
                + dependency_score * 0.4
            )

            if temporal_gap < 0:
                temporal_explanation = (
                    f"{related_service} anomaly occurred "
                    f"{abs(temporal_gap):.1f} seconds before "
                    f"the incident."
                )
            else:
                temporal_explanation = (
                    f"{related_service} anomaly occurred "
                    f"{temporal_gap:.1f} seconds after "
                    f"the incident."
                )

            explanation = (
                f"{relationship} dependency detected. "
                f"{temporal_explanation}"
            )

            results.append(
                {
                    "incident_id": incident.id,
                    "service_id": incident.service_id,
                    "related_service_id": related_service,
                    "relationship": relationship,
                    "temporal_gap_seconds": temporal_gap,
                    "evidence_count": evidence_count,
                    "correlation_score": correlation_score,
                    "explanation": explanation,
                }
            )

        results.sort(
            key=lambda item: item["correlation_score"],
            reverse=True,
        )

        return results


correlation_engine = CorrelationEngine()