from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.security import require_admin_api_key
admin: str = Depends(require_admin_api_key)
from app.api.schemas import (
    ChaosExperimentCreate,
    ChaosExperimentResponse,
    ChaosStartResponse,
)
from app.db.database import get_db
from app.models.chaos_experiment import ChaosExperiment
from app.services.chaos_engine import (
    ChaosValidationError,
    chaos_engine,
)


router = APIRouter(
    prefix="/chaos",
    tags=["Chaos Engineering"],
)


@router.post(
    "/experiments",
    response_model=ChaosExperimentResponse,
)
def create_experiment(
    payload: ChaosExperimentCreate,
    db: Session = Depends(get_db),
):
    try:
        return chaos_engine.create_experiment(
            db=db,
            target_service_id=payload.target_service_id,
            failure_type=payload.failure_type,
            intensity=payload.intensity,
            duration_seconds=payload.duration_seconds,
        )
    except ChaosValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/experiments",
    response_model=list[ChaosExperimentResponse],
)
def list_experiments(
    db: Session = Depends(get_db),
):
    return (
        db.query(ChaosExperiment)
        .order_by(
            ChaosExperiment.created_at.desc()
        )
        .all()
    )


@router.get(
    "/experiments/{experiment_id}",
    response_model=ChaosExperimentResponse,
)
def get_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
):
    experiment = chaos_engine.get_experiment(
        db,
        experiment_id,
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Chaos experiment not found.",
        )

    return experiment


@router.post(
    "/experiments/{experiment_id}/start",
    response_model=ChaosStartResponse,
)
def start_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
):
    experiment = chaos_engine.get_experiment(
        db,
        experiment_id,
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Chaos experiment not found.",
        )

    try:
        result = chaos_engine.start_experiment(
            db,
            experiment,
        )
    except ChaosValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return result


@router.post(
    "/experiments/{experiment_id}/complete",
    response_model=ChaosExperimentResponse,
)
def complete_experiment(
    experiment_id: str,
    incident_created: bool = False,
    recovery_time_seconds: float | None = None,
    db: Session = Depends(get_db),
):
    experiment = chaos_engine.get_experiment(
        db,
        experiment_id,
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Chaos experiment not found.",
        )

    try:
        return chaos_engine.complete_experiment(
            db,
            experiment,
            incident_created,
            recovery_time_seconds,
        )
    except ChaosValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "/experiments/{experiment_id}/fail",
    response_model=ChaosExperimentResponse,
)
def fail_experiment(
    experiment_id: str,
    reason: str,
    db: Session = Depends(get_db),
):
    experiment = chaos_engine.get_experiment(
        db,
        experiment_id,
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Chaos experiment not found.",
        )

    try:
        return chaos_engine.fail_experiment(
            db,
            experiment,
            reason,
        )
    except ChaosValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )