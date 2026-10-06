from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.incident_timeline import IncidentTimelineEvent


VALID_STATUSES = {
    "DETECTED",
    "TRIAGED",
    "INVESTIGATING",
    "ROOT_CAUSE_IDENTIFIED",
    "REMEDIATION_PENDING",
    "REMEDIATING",
    "VERIFYING",
    "RESOLVED",
    "FAILED",
    "CANCELLED",
}


ALLOWED_TRANSITIONS = {
    "DETECTED": {
        "TRIAGED",
        "CANCELLED",
    },
    "TRIAGED": {
        "INVESTIGATING",
        "CANCELLED",
    },
    "INVESTIGATING": {
        "ROOT_CAUSE_IDENTIFIED",
        "FAILED",
        "CANCELLED",
    },
    "ROOT_CAUSE_IDENTIFIED": {
        "REMEDIATION_PENDING",
        "RESOLVED",
        "FAILED",
    },
    "REMEDIATION_PENDING": {
        "REMEDIATING",
        "CANCELLED",
    },
    "REMEDIATING": {
        "VERIFYING",
        "FAILED",
    },
    "VERIFYING": {
        "RESOLVED",
        "FAILED",
        "REMEDIATING",
    },
    "RESOLVED": set(),
    "FAILED": set(),
    "CANCELLED": set(),
}


def generate_incident_key() -> str:
    return f"INC-{uuid4().hex[:10].upper()}"


def validate_status(status: str) -> str:
    normalized = status.upper()

    if normalized not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid incident status: {status}",
        )

    return normalized


def transition_incident(
    db: Session,
    incident: Incident,
    new_status: str,
) -> Incident:

    new_status = validate_status(new_status)

    current_status = incident.status

    if current_status == new_status:
        return incident

    allowed = ALLOWED_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Invalid incident transition: "
                f"{current_status} -> {new_status}"
            ),
        )

    now = datetime.now(timezone.utc)

    incident.status = new_status

    if new_status == "TRIAGED":
        incident.acknowledged_at = now

    if new_status == "RESOLVED":
        incident.resolved_at = now

    timeline_event = IncidentTimelineEvent(
        incident_id=incident.id,
        event_type="STATUS_CHANGE",
        previous_status=current_status,
        new_status=new_status,
        message=(
            f"Incident status changed from "
            f"{current_status} to {new_status}."
        ),
        created_at=now,
    )

    db.add(timeline_event)
    db.commit()
    db.refresh(incident)

    return incident