from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.schemas import (
    IncidentCreate,
    IncidentResponse,
    IncidentTimelineResponse,
    IncidentUpdate,
)
from app.db.database import get_db
from app.models.anomaly import Anomaly
from app.models.incident import Incident
from app.models.incident_timeline import IncidentTimelineEvent
from app.services.incident_manager import (
    generate_incident_key,
    transition_incident,
)

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=201,
)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
):
    incident = Incident(
        incident_key=generate_incident_key(),
        title=payload.title,
        description=payload.description,
        service_id=payload.service_id,
        environment=payload.environment,
        severity=payload.severity.upper(),
        status="DETECTED",
        source=payload.source,
        anomaly_id=payload.anomaly_id,
        detected_at=datetime.now(timezone.utc),
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    timeline = IncidentTimelineEvent(
        incident_id=incident.id,
        event_type="INCIDENT_CREATED",
        previous_status=None,
        new_status="DETECTED",
        message="Incident created.",
        created_at=datetime.now(timezone.utc),
    )

    db.add(timeline)
    db.commit()

    return incident


@router.post(
    "/from-anomaly/{anomaly_id}",
    response_model=IncidentResponse,
    status_code=201,
)
def create_incident_from_anomaly(
    anomaly_id: int,
    db: Session = Depends(get_db),
):
    anomaly = db.get(Anomaly, anomaly_id)

    if anomaly is None:
        raise HTTPException(
            status_code=404,
            detail="Anomaly not found.",
        )

    existing = db.scalar(
        select(Incident)
        .where(Incident.anomaly_id == anomaly_id)
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "An incident already exists for this anomaly.",
                "incident_key": existing.incident_key,
            },
        )

    incident = Incident(
        incident_key=generate_incident_key(),
        title=(
            f"{anomaly.severity} anomaly detected in "
            f"{anomaly.service_id}"
        ),
        description=anomaly.reason,
        service_id=anomaly.service_id,
        environment=anomaly.environment,
        severity=anomaly.severity,
        status="DETECTED",
        source="anomaly_detection",
        anomaly_id=anomaly.id,
        detected_at=anomaly.detected_at,
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    timeline = IncidentTimelineEvent(
        incident_id=incident.id,
        event_type="ANOMALY_DETECTED",
        previous_status=None,
        new_status="DETECTED",
        message=(
            f"Incident created automatically from anomaly "
            f"{anomaly.id}."
        ),
        created_at=datetime.now(timezone.utc),
    )

    db.add(timeline)
    db.commit()

    return incident


@router.get(
    "",
    response_model=list[IncidentResponse],
)
def list_incidents(
    service_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    statement = select(Incident)

    if service_id:
        statement = statement.where(
            Incident.service_id == service_id
        )

    if status:
        statement = statement.where(
            Incident.status == status.upper()
        )

    if severity:
        statement = statement.where(
            Incident.severity == severity.upper()
        )

    if environment:
        statement = statement.where(
            Incident.environment == environment
        )

    statement = (
        statement
        .order_by(desc(Incident.detected_at))
        .limit(limit)
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    return incident


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
)
def update_incident(
    incident_id: int,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    if payload.severity is not None:
        incident.severity = payload.severity.upper()

    if payload.description is not None:
        incident.description = payload.description

    if payload.confidence is not None:
        if not 0 <= payload.confidence <= 1:
            raise HTTPException(
                status_code=400,
                detail="Confidence must be between 0 and 1.",
            )

        incident.confidence = payload.confidence

    db.commit()
    db.refresh(incident)

    if payload.status is not None:
        incident = transition_incident(
            db,
            incident,
            payload.status,
        )

    return incident


@router.get(
    "/{incident_id}/timeline",
    response_model=list[IncidentTimelineResponse],
)
def get_incident_timeline(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    statement = (
        select(IncidentTimelineEvent)
        .where(
            IncidentTimelineEvent.incident_id == incident_id
        )
        .order_by(
            IncidentTimelineEvent.created_at.asc()
        )
    )

    return list(db.scalars(statement).all())