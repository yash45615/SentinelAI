from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    RecoveryCheckResponse,
    RecoveryVerificationResponse,
)
from app.db.database import get_db
from app.models.incident import Incident
from app.models.recovery_check import RecoveryCheck
from app.models.remediation_action import RemediationAction
from app.services.recovery_verifier import recovery_verifier


router = APIRouter(
    prefix="/incidents",
    tags=["Recovery Verification"],
)


@router.post(
    "/{incident_id}/recovery/check",
    response_model=RecoveryVerificationResponse,
)
def verify_recovery(
    incident_id: int,
    remediation_action_id: int | None = None,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    if remediation_action_id is not None:
        action = db.get(
            RemediationAction,
            remediation_action_id,
        )

        if action is None:
            raise HTTPException(
                status_code=404,
                detail="Remediation action not found.",
            )

        if action.incident_id != incident.id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Remediation action does not belong "
                    "to this incident."
                ),
            )

    results = recovery_verifier.run_checks(
        db,
        incident,
        remediation_action_id,
    )

    overall_status = recovery_verifier.summarize(
        results
    )

    if overall_status == "PASSED":
        if incident.status == "VERIFYING":
            incident.status = "RESOLVED"

    elif overall_status == "FAILED":
        if incident.status == "VERIFYING":
            incident.status = "REMEDIATING"

    db.commit()

    checks = (
        db.query(RecoveryCheck)
        .filter(
            RecoveryCheck.incident_id == incident.id
        )
        .order_by(
            RecoveryCheck.checked_at.desc()
        )
        .limit(len(results))
        .all()
    )

    return RecoveryVerificationResponse(
        incident_id=incident.id,
        remediation_action_id=remediation_action_id,
        overall_status=overall_status,
        checks=checks,
    )


@router.get(
    "/{incident_id}/recovery",
    response_model=list[RecoveryCheckResponse],
)
def get_recovery_checks(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    return (
        db.query(RecoveryCheck)
        .filter(
            RecoveryCheck.incident_id == incident_id
        )
        .order_by(
            RecoveryCheck.checked_at.desc()
        )
        .all()
    )


@router.get(
    "/{incident_id}/recovery/status",
)
def get_recovery_status(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    recovery_status = recovery_verifier.get_status(
        db,
        incident_id,
    )

    return {
        "incident_id": incident_id,
        "incident_status": incident.status,
        "recovery_status": recovery_status,
    }