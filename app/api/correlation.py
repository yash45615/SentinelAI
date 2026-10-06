from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    CorrelationResponse,
    IncidentTimelineEventResponse,
)
from app.db.database import get_db
from app.models.incident import Incident
from app.services.correlation_engine import correlation_engine
from app.services.timeline_builder import timeline_builder


router = APIRouter(
    prefix="/incidents",
    tags=["Correlation"],
)


@router.get(
    "/{incident_id}/correlations",
    response_model=list[CorrelationResponse],
)
def get_incident_correlations(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    return correlation_engine.correlate_incident(
        db,
        incident,
    )


@router.get(
    "/{incident_id}/timeline/reconstructed",
    response_model=list[IncidentTimelineEventResponse],
)
def get_reconstructed_timeline(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    return timeline_builder.build(
        db,
        incident,
    )