from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import SloResultResponse
from app.db.database import get_db
from app.models.service import Service
from app.models.slo_result import SloResult
from app.services.slo_engine import slo_engine


router = APIRouter(
    prefix="/slo",
    tags=["SLO & Reliability"],
)


@router.post(
    "/services/{service_id}/calculate",
    response_model=SloResultResponse,
)
def calculate_service_slo(
    service_id: str,
    window_minutes: int = 60,
    environment: str = "production",
    db: Session = Depends(get_db),
):
    service = (
        db.query(Service)
        .filter(
            Service.service_id == service_id
        )
        .first()
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found.",
        )

    try:
        return slo_engine.calculate_service_slo(
            db=db,
            service_id=service_id,
            window_minutes=window_minutes,
            environment=environment,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/services/{service_id}/latest",
    response_model=SloResultResponse,
)
def get_latest_slo(
    service_id: str,
    db: Session = Depends(get_db),
):
    service = (
        db.query(Service)
        .filter(
            Service.service_id == service_id
        )
        .first()
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found.",
        )

    result = slo_engine.get_latest(
        db,
        service_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No SLO calculation exists.",
        )

    return result


@router.get(
    "/services/{service_id}/history",
    response_model=list[SloResultResponse],
)
def get_slo_history(
    service_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    service = (
        db.query(Service)
        .filter(
            Service.service_id == service_id
        )
        .first()
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found.",
        )

    if limit <= 0 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100.",
        )

    return (
        db.query(SloResult)
        .filter(
            SloResult.service_id == service_id
        )
        .order_by(
            SloResult.calculated_at.desc()
        )
        .limit(limit)
        .all()
    )


@router.get(
    "/targets",
)
def get_slo_targets():
    return {
        "availability_percent": (
            slo_engine.AVAILABILITY_TARGET
        ),
        "error_rate_percent": (
            slo_engine.ERROR_RATE_TARGET
        ),
        "p95_latency_ms": (
            slo_engine.P95_LATENCY_TARGET_MS
        ),
        "incident_detection_seconds": (
            slo_engine.DETECTION_TARGET_SECONDS
        ),
        "recovery_verification_seconds": (
            slo_engine.RECOVERY_TARGET_SECONDS
        ),
    }