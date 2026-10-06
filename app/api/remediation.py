from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.security import require_admin_api_key
from app.api.schemas import (
    RemediationActionCreate,
    RemediationActionResponse,
)
from app.db.database import get_db
from app.models.incident import Incident
from app.models.remediation_action import RemediationAction
from app.services.remediation_engine import remediation_engine


router = APIRouter(
    prefix="/incidents",
    tags=["Remediation"],
)


@router.post(
    "/{incident_id}/remediation",
    response_model=RemediationActionResponse,
    status_code=201,
)
def create_remediation_action(
    incident_id: int,
    payload: RemediationActionCreate,
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

    try:
        action = remediation_engine.create_action(
            db=db,
            incident=incident,
            service_id=payload.service_id,
            action_type=payload.action_type,
            reason=payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return action


@router.post(
    "/{incident_id}/remediation/{action_id}/execute",
    response_model=RemediationActionResponse,
)
def execute_remediation_action(
    incident_id: int,
    action_id: int,
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

    action = db.get(
        RemediationAction,
        action_id,
    )

    if action is None:
        raise HTTPException(
            status_code=404,
            detail="Remediation action not found.",
        )

    if action.incident_id != incident_id:
        raise HTTPException(
            status_code=400,
            detail="Remediation action does not belong to this incident.",
        )

    try:
        remediation_engine.execute_action(
            db=db,
            action=action,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return action


@router.get(
    "/{incident_id}/remediation",
    response_model=list[RemediationActionResponse],
)
def list_remediation_actions(
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
        select(RemediationAction)
        .where(
            RemediationAction.incident_id == incident_id
        )
        .order_by(
            desc(RemediationAction.requested_at)
        )
    )

    return list(
        db.scalars(statement).all()
    )


@router.get(
    "/{incident_id}/remediation/{action_id}",
    response_model=RemediationActionResponse,
)
def get_remediation_action(
    incident_id: int,
    action_id: int,
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

    action = db.get(
        RemediationAction,
        action_id,
    )

    if action is None:
        raise HTTPException(
            status_code=404,
            detail="Remediation action not found.",
        )

    if action.incident_id != incident_id:
        raise HTTPException(
            status_code=400,
            detail="Remediation action does not belong to this incident.",
        )

    return action