from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas import (
    DependencyCreate,
    DependencyResponse,
)
from app.db.database import get_db
from app.models.dependency import ServiceDependency


router = APIRouter(
    prefix="/dependencies",
    tags=["Dependencies"],
)


@router.post(
    "",
    response_model=DependencyResponse,
    status_code=201,
)
def create_dependency(
    payload: DependencyCreate,
    db: Session = Depends(get_db),
):
    if payload.source_service_id == payload.target_service_id:
        raise HTTPException(
            status_code=400,
            detail="A service cannot depend on itself.",
        )

    existing = db.scalar(
        select(ServiceDependency).where(
            ServiceDependency.source_service_id
            == payload.source_service_id,
            ServiceDependency.target_service_id
            == payload.target_service_id,
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Dependency already exists.",
        )

    dependency = ServiceDependency(
        source_service_id=payload.source_service_id,
        target_service_id=payload.target_service_id,
        dependency_type=payload.dependency_type.upper(),
        criticality=payload.criticality.upper(),
    )

    db.add(dependency)

    try:
        db.commit()
        db.refresh(dependency)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Dependency already exists.",
        )

    return dependency


@router.get(
    "",
    response_model=list[DependencyResponse],
)
def list_dependencies(
    source_service_id: str | None = Query(default=None),
    target_service_id: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    statement = select(ServiceDependency)

    if source_service_id:
        statement = statement.where(
            ServiceDependency.source_service_id
            == source_service_id
        )

    if target_service_id:
        statement = statement.where(
            ServiceDependency.target_service_id
            == target_service_id
        )

    if active_only:
        statement = statement.where(
            ServiceDependency.active.is_(True)
        )

    statement = statement.order_by(
        asc(ServiceDependency.source_service_id)
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{dependency_id}",
    response_model=DependencyResponse,
)
def get_dependency(
    dependency_id: int,
    db: Session = Depends(get_db),
):
    dependency = db.get(
        ServiceDependency,
        dependency_id,
    )

    if dependency is None:
        raise HTTPException(
            status_code=404,
            detail="Dependency not found.",
        )

    return dependency