from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.schemas import AnomalyResponse
from app.db.database import get_db
from app.models.anomaly import Anomaly
from app.services.anomaly_detector import detector


router = APIRouter(
    prefix="/detection",
    tags=["Detection"],
)


class DetectionRequest(BaseModel):
    service_id: str
    environment: str = "production"
    metric_name: str
    baseline_value: float = Field(gt=0)
    observed_value: float
    threshold_percent: float = Field(
        default=50.0,
        gt=0,
    )


class DetectionResponse(BaseModel):
    anomaly_detected: bool
    severity: str
    deviation_percent: float
    reason: str
    anomaly: AnomalyResponse | None = None


@router.post(
    "/detect",
    response_model=DetectionResponse,
)
def detect_anomaly(
    payload: DetectionRequest,
    db: Session = Depends(get_db),
):
    try:
        result = detector.detect(
            metric_name=payload.metric_name,
            baseline_value=payload.baseline_value,
            observed_value=payload.observed_value,
            threshold_percent=payload.threshold_percent,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if not result.is_anomaly:
        return DetectionResponse(
            anomaly_detected=False,
            severity=result.severity,
            deviation_percent=result.deviation_percent,
            reason=result.reason,
            anomaly=None,
        )

    anomaly = Anomaly(
        service_id=payload.service_id,
        environment=payload.environment,
        metric_name=payload.metric_name,
        observed_value=payload.observed_value,
        baseline_value=payload.baseline_value,
        deviation_percent=result.deviation_percent,
        threshold_percent=payload.threshold_percent,
        severity=result.severity,
        detection_method="percentage_threshold",
        reason=result.reason,
        detected_at=datetime.now(timezone.utc),
    )

    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)

    return DetectionResponse(
        anomaly_detected=True,
        severity=result.severity,
        deviation_percent=result.deviation_percent,
        reason=result.reason,
        anomaly=anomaly,
    )