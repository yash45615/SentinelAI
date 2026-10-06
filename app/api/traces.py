from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas import TraceCreate, TraceResponse
from app.db.database import get_db
from app.models.trace import TraceSpan


router = APIRouter(
    prefix="/traces",
    tags=["Traces"],
)


@router.post(
    "",
    response_model=TraceResponse,
    status_code=201,
)
def create_trace_span(
    payload: TraceCreate,
    db: Session = Depends(get_db),
):
    existing_span = db.scalar(
        select(TraceSpan).where(
            TraceSpan.span_id == payload.span_id
        )
    )

    if existing_span is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Span already exists.",
                "span_id": payload.span_id,
                "existing_trace_id": existing_span.trace_id,
            },
        )

    span = TraceSpan(
        trace_id=payload.trace_id,
        span_id=payload.span_id,
        parent_span_id=payload.parent_span_id,
        request_id=payload.request_id,
        service_id=payload.service_id,
        operation=payload.operation,
        start_time=payload.start_time,
        end_time=payload.end_time,
        duration_ms=payload.duration_ms,
        status_code=payload.status_code,
        status=payload.status,
    )

    db.add(span)

    try:
        db.commit()
        db.refresh(span)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Trace span already exists.",
        )

    return span


@router.get(
    "",
    response_model=list[TraceResponse],
)
def list_traces(
    trace_id: str | None = Query(default=None),
    service_id: str | None = Query(default=None),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
    db: Session = Depends(get_db),
):
    statement = select(TraceSpan)

    if trace_id:
        statement = statement.where(
            TraceSpan.trace_id == trace_id
        )

    if service_id:
        statement = statement.where(
            TraceSpan.service_id == service_id
        )

    statement = statement.order_by(
        asc(TraceSpan.start_time)
    ).limit(limit)

    return list(
        db.scalars(statement).all()
    )


@router.get(
    "/{trace_id}",
    response_model=list[TraceResponse],
)
def get_trace(
    trace_id: str,
    db: Session = Depends(get_db),
):
    statement = (
        select(TraceSpan)
        .where(
            TraceSpan.trace_id == trace_id
        )
        .order_by(
            asc(TraceSpan.start_time)
        )
    )

    return list(
        db.scalars(statement).all()
    )