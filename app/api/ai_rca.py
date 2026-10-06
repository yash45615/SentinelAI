from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.schemas import AiRcaAnalysisResponse
from app.db.database import get_db
from app.models.ai_rca_analysis import AiRcaAnalysis
from app.models.incident import Incident
from app.models.incident_evidence import IncidentEvidence
from app.models.rca_hypothesis import RcaHypothesis
from app.services.ai_rca_assistant import ai_rca_assistant
from app.services.rca_engine import rca_engine


router = APIRouter(
    prefix="/incidents",
    tags=["AI RCA"],
)


@router.post(
    "/{incident_id}/rca/ai-analyze",
    response_model=AiRcaAnalysisResponse,
    status_code=201,
)
def analyze_incident_with_ai(
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

    hypotheses = rca_engine.analyze_incident(
        db,
        incident,
    )

    evidence_statement = (
        select(IncidentEvidence)
        .where(
            IncidentEvidence.incident_id == incident_id
        )
        .order_by(
            desc(IncidentEvidence.relevance_score)
        )
    )

    evidence = list(
        db.scalars(evidence_statement).all()
    )

    result = ai_rca_assistant.analyze(
        incident=incident,
        hypotheses=hypotheses,
        evidence=evidence,
    )

    analysis = AiRcaAnalysis(
        incident_id=incident_id,
        selected_hypothesis_id=result.selected_hypothesis_id,
        provider=result.provider,
        model=result.model,
        summary=result.summary,
        root_cause=result.root_cause,
        reasoning=result.reasoning,
        recommended_action=result.recommended_action,
        confidence=result.confidence,
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return analysis


@router.get(
    "/{incident_id}/rca/ai",
    response_model=list[AiRcaAnalysisResponse],
)
def get_ai_rca_analyses(
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
        select(AiRcaAnalysis)
        .where(
            AiRcaAnalysis.incident_id == incident_id
        )
        .order_by(
            desc(AiRcaAnalysis.generated_at)
        )
    )

    return list(
        db.scalars(statement).all()
    )


@router.get(
    "/{incident_id}/rca/ai/latest",
    response_model=AiRcaAnalysisResponse,
)
def get_latest_ai_rca(
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
        select(AiRcaAnalysis)
        .where(
            AiRcaAnalysis.incident_id == incident_id
        )
        .order_by(
            desc(AiRcaAnalysis.generated_at)
        )
        .limit(1)
    )

    analysis = db.scalars(statement).first()

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="AI RCA analysis not found.",
        )

    return analysis