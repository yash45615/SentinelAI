from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.api.schemas import IncidentEvidenceResponse
from app.db.database import get_db
from app.models.incident import Incident
from app.models.incident_evidence import IncidentEvidence
from app.services.evidence_collector import evidence_collector


router = APIRouter(
    prefix="/incidents",
    tags=["Incident Evidence"],
)


@router.post(
    "/{incident_id}/evidence/collect",
    response_model=list[IncidentEvidenceResponse],
)
def collect_incident_evidence(
    incident_id: int,
    before_minutes: int = Query(
        default=5,
        ge=0,
        le=60,
    ),
    after_minutes: int = Query(
        default=5,
        ge=0,
        le=60,
    ),
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

    evidence = evidence_collector.collect(
        db=db,
        incident=incident,
        before_minutes=before_minutes,
        after_minutes=after_minutes,
    )

    return evidence


@router.get(
    "/{incident_id}/evidence",
    response_model=list[IncidentEvidenceResponse],
)
def list_incident_evidence(
    incident_id: int,
    evidence_type: str | None = Query(
        default=None
    ),
    service_id: str | None = Query(
        default=None
    ),
    min_relevance: float | None = Query(
        default=None,
        ge=0,
        le=1,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
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

    statement = select(
        IncidentEvidence
    ).where(
        IncidentEvidence.incident_id == incident_id
    )

    if evidence_type:
        statement = statement.where(
            IncidentEvidence.evidence_type
            == evidence_type.upper()
        )

    if service_id:
        statement = statement.where(
            IncidentEvidence.service_id
            == service_id
        )

    if min_relevance is not None:
        statement = statement.where(
            IncidentEvidence.relevance_score
            >= min_relevance
        )

    statement = (
        statement
        .order_by(
            asc(
                IncidentEvidence.evidence_timestamp
            )
        )
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )


@router.get(
    "/{incident_id}/evidence/{evidence_id}",
    response_model=IncidentEvidenceResponse,
)
def get_incident_evidence(
    incident_id: int,
    evidence_id: int,
    db: Session = Depends(get_db),
):
    evidence = db.scalar(
        select(IncidentEvidence).where(
            IncidentEvidence.id == evidence_id,
            IncidentEvidence.incident_id == incident_id,
        )
    )

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found.",
        )

    return evidence