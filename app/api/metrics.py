from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.schemas import MetricCreate, MetricResponse
from app.db.database import get_db
from app.models.metric import MetricSample


router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"],
)


@router.post(
    "",
    response_model=MetricResponse,
    status_code=201,
)
def create_metric(
    payload: MetricCreate,
    db: Session = Depends(get_db),
):
    metric = MetricSample(
        service_id=payload.service_id,
        environment=payload.environment,
        metric_name=payload.metric_name,
        metric_type=payload.metric_type,
        value=payload.value,
        unit=payload.unit,
        timestamp=(
            payload.timestamp
            or datetime.now(timezone.utc)
        ),
    )

    db.add(metric)
    db.commit()
    db.refresh(metric)

    return metric


@router.get(
    "",
    response_model=list[MetricResponse],
)
def list_metrics(
    service_id: str | None = Query(default=None),
    metric_name: str | None = Query(default=None),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
    db: Session = Depends(get_db),
):
    statement = select(MetricSample)

    if service_id:
        statement = statement.where(
            MetricSample.service_id == service_id
        )

    if metric_name:
        statement = statement.where(
            MetricSample.metric_name == metric_name
        )

    statement = statement.order_by(
        desc(MetricSample.timestamp)
    ).limit(limit)

    return list(
        db.scalars(statement).all()
    )


@router.get(
    "/{metric_id}",
    response_model=MetricResponse,
)
def get_metric(
    metric_id: int,
    db: Session = Depends(get_db),
):
    metric = db.get(
        MetricSample,
        metric_id,
    )

    if metric is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Metric not found.",
        )

    return metric