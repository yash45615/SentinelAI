from datetime import timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.anomaly import Anomaly
from app.models.incident import Incident
from app.models.incident_evidence import IncidentEvidence


class TimelineBuilder:

    def build(
        self,
        db: Session,
        incident: Incident,
    ) -> list[dict]:

        events = []

        incident_time = incident.detected_at

        if incident_time.tzinfo is None:
            incident_time = incident_time.replace(
                tzinfo=timezone.utc
            )

        anomalies = list(
            db.scalars(
                select(Anomaly).where(
                    Anomaly.service_id
                    == incident.service_id
                )
            ).all()
        )

        for anomaly in anomalies:

            event_time = anomaly.detected_at

            if event_time.tzinfo is None:
                event_time = event_time.replace(
                    tzinfo=timezone.utc
                )

            events.append(
                {
                    "timestamp": event_time,
                    "event_type": "ANOMALY",
                    "service_id": anomaly.service_id,
                    "description": (
                        f"{anomaly.metric_name} deviated "
                        f"{anomaly.deviation_percent:.2f}% "
                        f"from baseline."
                    ),
                }
            )

        evidence = list(
            db.scalars(
                select(IncidentEvidence).where(
                    IncidentEvidence.incident_id
                    == incident.id
                )
            ).all()
        )

        for item in evidence:

            event_time = item.evidence_timestamp

            if event_time.tzinfo is None:
                event_time = event_time.replace(
                    tzinfo=timezone.utc
                )

            events.append(
                {
                    "timestamp": event_time,
                    "event_type": item.evidence_type,
                    "service_id": item.service_id,
                    "description": item.summary,
                }
            )

        events.append(
            {
                "timestamp": incident_time,
                "event_type": "INCIDENT",
                "service_id": incident.service_id,
                "description": incident.title,
            }
        )

        events.sort(
            key=lambda event: event["timestamp"]
        )

        return events


timeline_builder = TimelineBuilder()