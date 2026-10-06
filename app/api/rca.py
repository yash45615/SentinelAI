from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.api.schemas import RcaHypothesisResponse
from app.db.database import get_db
from app.models.incident import Incident
from app.models.rca_hypothesis import RcaHypothesis
from app.services.rca_engine import rca_engine


router = APIRouter(
    prefix="/incidents",
    tags=["RCA"],
)


@router.post(
    "/{incident_id}/rca/analyze",
    response_model=list[RcaHypothesisResponse],
)
def analyze_incident_rca(
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

    return rca_engine.analyze_incident(
        db,
        incident,
    )


@router.get(
    "/{incident_id}/rca",
    response_model=list[RcaHypothesisResponse],
)
def get_incident_rca(
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

    statement = (
        select(RcaHypothesis)
        .where(
            RcaHypothesis.incident_id
            == incident_id
        )
        .order_by(
            asc(RcaHypothesis.rank)
        )
    )

    return list(
        db.scalars(
            statement
        ).all()
    )


@router.get(
    "/{incident_id}/rca/top",
    response_model=RcaHypothesisResponse,
)
def get_top_rca(
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

    statement = (
        select(RcaHypothesis)
        .where(
            RcaHypothesis.incident_id
            == incident_id
        )
        .order_by(
            asc(RcaHypothesis.rank)
        )
        .limit(1)
    )

    hypothesis = db.scalar(
        statement
    )

    if hypothesis is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "RCA analysis has not been generated."
            ),
        )

    return hypothesis