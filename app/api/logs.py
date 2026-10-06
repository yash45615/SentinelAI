from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.schemas import LogCreate, LogResponse
from app.db.database import get_db
from app.models.log import LogEvent


router = APIRouter(
    prefix="/logs",
    tags=["Logs"],
)


@router.post(
    "",
    response_model=LogResponse,
    status_code=201,
)
def create_log(
    payload: LogCreate,
    db: Session = Depends(get_db),
):
    log = LogEvent(
        request_id=payload.request_id,
        trace_id=payload.trace_id,
        service_id=payload.service_id,
        environment=payload.environment,
        level=payload.level.upper(),
        event_type=payload.event_type,
        message=payload.message,
        endpoint=payload.endpoint,
        status_code=payload.status_code,
        timestamp=(
            payload.timestamp
            or datetime.now(timezone.utc)
        ),
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log


@router.get(
    "",
    response_model=list[LogResponse],
)
def list_logs(
    service_id: str | None = Query(default=None),
    level: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    trace_id: str | None = Query(default=None),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
    db: Session = Depends(get_db),
):
    statement = select(LogEvent)

    if service_id:
        statement = statement.where(
            LogEvent.service_id == service_id
        )

    if level:
        statement = statement.where(
            LogEvent.level == level.upper()
        )

    if event_type:
        statement = statement.where(
            LogEvent.event_type == event_type
        )

    if request_id:
        statement = statement.where(
            LogEvent.request_id == request_id
        )

    if trace_id:
        statement = statement.where(
            LogEvent.trace_id == trace_id
        )

    statement = statement.order_by(
        desc(LogEvent.timestamp)
    ).limit(limit)

    return list(
        db.scalars(statement).all()
    )


@router.get(
    "/{log_id}",
    response_model=LogResponse,
)
def get_log(
    log_id: int,
    db: Session = Depends(get_db),
):
    log = db.get(
        LogEvent,
        log_id,
    )

    if log is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Log event not found.",
        )

    return log