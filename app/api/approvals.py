from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.security import require_admin_api_key
from app.api.schemas import (
    ApprovalDecision,
    ApprovalRequestCreate,
    RemediationApprovalResponse,
)
from app.db.database import get_db
from app.models.incident import Incident
from app.models.remediation_action import RemediationAction
from app.models.remediation_approval import RemediationApproval
from app.services.approval_gateway import approval_gateway


router = APIRouter(
    prefix="/incidents",
    tags=["Approval Gateway"],
)


@router.post(
    "/{incident_id}/remediation/{action_id}/approval",
    response_model=RemediationApprovalResponse,
    status_code=201,
)
def request_remediation_approval(
    incident_id: int,
    action_id: int,
    payload: ApprovalRequestCreate,
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
        approval = approval_gateway.request_approval(
            db=db,
            incident=incident,
            action=action,
            requested_by=payload.requested_by,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return approval


@router.post(
    "/{incident_id}/remediation/{action_id}/approval/approve",
    response_model=RemediationApprovalResponse,
)
def approve_remediation(
    incident_id: int,
    action_id: int,
    payload: ApprovalDecision,
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

    statement = (
        select(RemediationApproval)
        .where(
            RemediationApproval.remediation_action_id
            == action_id
        )
        .order_by(
            desc(RemediationApproval.created_at)
        )
        .limit(1)
    )

    approval = db.scalars(statement).first()

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    try:
        approval = approval_gateway.approve(
            db=db,
            approval=approval,
            approved_by=payload.decided_by,
            decision_reason=payload.decision_reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return approval


@router.post(
    "/{incident_id}/remediation/{action_id}/approval/reject",
    response_model=RemediationApprovalResponse,
)
def reject_remediation(
    incident_id: int,
    action_id: int,
    payload: ApprovalDecision,
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

    statement = (
        select(RemediationApproval)
        .where(
            RemediationApproval.remediation_action_id
            == action_id
        )
        .order_by(
            desc(RemediationApproval.created_at)
        )
        .limit(1)
    )

    approval = db.scalars(statement).first()

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    try:
        approval = approval_gateway.reject(
            db=db,
            approval=approval,
            rejected_by=payload.decided_by,
            decision_reason=payload.decision_reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return approval


@router.get(
    "/{incident_id}/remediation/{action_id}/approval",
    response_model=list[RemediationApprovalResponse],
)
def list_action_approvals(
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

    statement = (
        select(RemediationApproval)
        .where(
            RemediationApproval.remediation_action_id
            == action_id
        )
        .order_by(
            desc(RemediationApproval.created_at)
        )
    )

    return list(
        db.scalars(statement).all()
    )