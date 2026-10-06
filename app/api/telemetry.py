from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.schemas import TelemetryCreate, TelemetryResponse
from app.db.database import get_db
from app.models.telemetry import TelemetryEvent

router = APIRouter(
    prefix="/telemetry",
    tags=["Telemetry"],
)


@router.post(
    "",
    response_model=TelemetryResponse,
    status_code=201,
)
def create_telemetry(
    payload: TelemetryCreate,
    db: Session = Depends(get_db),
):
    event = TelemetryEvent(
        request_id=payload.request_id,
        trace_id=payload.trace_id,
        service_id=payload.service_id,
        environment=payload.environment,
        method=payload.method,
        endpoint=payload.endpoint,
        status_code=payload.status_code,
        latency_ms=payload.latency_ms,
        success=payload.success,
        error_type=payload.error_type,
        error_message=payload.error_message,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


@router.get(
    "",
    response_model=list[TelemetryResponse],
)
def list_telemetry(
    service_id: str | None = Query(default=None),
    status_code: int | None = Query(default=None),
    success: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    statement = select(TelemetryEvent)

    if service_id:
        statement = statement.where(
            TelemetryEvent.service_id == service_id
        )

    if status_code is not None:
        statement = statement.where(
            TelemetryEvent.status_code == status_code
        )

    if success is not None:
        statement = statement.where(
            TelemetryEvent.success == success
        )

    statement = statement.order_by(
        desc(TelemetryEvent.timestamp)
    ).limit(limit)

    return list(db.scalars(statement).all())


@router.get(
    "/{telemetry_id}",
    response_model=TelemetryResponse,
)
def get_telemetry(
    telemetry_id: int,
    db: Session = Depends(get_db),
):
    event = db.get(TelemetryEvent, telemetry_id)

    if event is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Telemetry event not found.",
        )

    return event