from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.schemas import AnomalyResponse
from app.db.database import get_db
from app.models.anomaly import Anomaly

router = APIRouter(
    prefix="/anomalies",
    tags=["Anomalies"],
)


@router.get("", response_model=list[AnomalyResponse])
def list_anomalies(
    service_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    metric_name: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    statement = select(Anomaly)

    if service_id:
        statement = statement.where(
            Anomaly.service_id == service_id
        )

    if severity:
        statement = statement.where(
            Anomaly.severity == severity.upper()
        )

    if metric_name:
        statement = statement.where(
            Anomaly.metric_name == metric_name
        )

    if environment:
        statement = statement.where(
            Anomaly.environment == environment
        )

    statement = (
        statement
        .order_by(desc(Anomaly.detected_at))
        .limit(limit)
    )

    return list(db.scalars(statement).all())


@router.get("/{anomaly_id}", response_model=AnomalyResponse)
def get_anomaly(
    anomaly_id: int,
    db: Session = Depends(get_db),
):
    anomaly = db.get(Anomaly, anomaly_id)

    if anomaly is None:
        raise HTTPException(
            status_code=404,
            detail="Anomaly not found.",
        )

    return anomaly