from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    LoadTestRequest,
    LoadTestResultResponse,
)
from app.db.database import get_db
from app.models.load_test_result import LoadTestResult
from app.models.service import Service
from app.services.load_test_engine import (
    load_test_engine,
)


router = APIRouter(
    prefix="/load-tests",
    tags=["Load Testing"],
)


@router.post(
    "/run",
    response_model=LoadTestResultResponse,
)
async def run_load_test(
    payload: LoadTestRequest,
    db: Session = Depends(get_db),
):
    service = (
        db.query(Service)
        .filter(
            Service.service_id
            == payload.service_id
        )
        .first()
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found.",
        )

    try:
        result = await load_test_engine.run(
            base_url=payload.base_url,
            service_id=payload.service_id,
            endpoint=payload.endpoint,
            concurrency=payload.concurrency,
            duration_seconds=(
                payload.duration_seconds
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    record = LoadTestResult(
        test_id=result.test_id,
        service_id=result.service_id,
        endpoint=result.endpoint,
        concurrency=result.concurrency,
        duration_seconds=result.duration_seconds,
        total_requests=result.total_requests,
        successful_requests=(
            result.successful_requests
        ),
        failed_requests=result.failed_requests,
        requests_per_second=(
            result.requests_per_second
        ),
        p50_latency_ms=result.p50_latency_ms,
        p95_latency_ms=result.p95_latency_ms,
        p99_latency_ms=result.p99_latency_ms,
        error_rate_percent=(
            result.error_rate_percent
        ),
        performance_status=(
            result.performance_status
        ),
        gate_reason=result.gate_reason,
        started_at=result.started_at,
        completed_at=result.completed_at,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get(
    "/",
    response_model=list[LoadTestResultResponse],
)
def list_load_tests(
    service_id: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    if limit <= 0 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100.",
        )

    query = db.query(LoadTestResult)

    if service_id:
        query = query.filter(
            LoadTestResult.service_id
            == service_id
        )

    return (
        query
        .order_by(
            LoadTestResult.created_at.desc()
        )
        .limit(limit)
        .all()
    )


@router.get(
    "/{test_id}",
    response_model=LoadTestResultResponse,
)
def get_load_test(
    test_id: str,
    db: Session = Depends(get_db),
):
    result = (
        db.query(LoadTestResult)
        .filter(
            LoadTestResult.test_id
            == test_id
        )
        .first()
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Load test not found.",
        )

    return result