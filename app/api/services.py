from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.schemas import (
    ServiceCreate,
    ServiceHealthResponse,
    ServiceResponse,
    ServiceUpdate,
)
from app.db.database import get_db
from app.models.service import Service


router = APIRouter(
    prefix="/services",
    tags=["Services"],
)


def get_service_by_service_id(
    db: Session,
    service_id: str,
) -> Service | None:
    statement = select(Service).where(
        Service.service_id == service_id
    )

    return db.scalars(statement).first()


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=201,
)
def create_service(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
):
    existing_service = get_service_by_service_id(
        db,
        payload.service_id,
    )

    if existing_service is not None:
        raise HTTPException(
            status_code=409,
            detail="Service with this service_id already exists.",
        )

    service = Service(
        service_id=payload.service_id,
        name=payload.name,
        description=payload.description,
        environment=payload.environment,
        version=payload.version,
        is_active=True,
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    return service


@router.get(
    "",
    response_model=list[ServiceResponse],
)
def list_services(
    environment: str | None = Query(default=None),
    active_only: bool = Query(default=False),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    statement = select(Service)

    if environment:
        statement = statement.where(
            Service.environment == environment
        )

    if active_only:
        statement = statement.where(
            Service.is_active.is_(True)
        )

    if search:
        search_pattern = f"%{search}%"

        statement = statement.where(
            or_(
                Service.service_id.ilike(search_pattern),
                Service.name.ilike(search_pattern),
                Service.description.ilike(search_pattern),
            )
        )

    statement = statement.order_by(Service.id)

    return list(db.scalars(statement).all())


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
)
def get_service(
    service_id: str,
    db: Session = Depends(get_db),
):
    service = get_service_by_service_id(
        db,
        service_id,
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found.",
        )

    return service


@router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
)
def update_service(
    service_id: str,
    payload: ServiceUpdate,
    db: Session = Depends(get_db),
):
    service = get_service_by_service_id(
        db,
        service_id,
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found.",
        )

    update_data = payload.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)

    return service


@router.delete(
    "/{service_id}",
    status_code=204,
)
def deactivate_service(
    service_id: str,
    db: Session = Depends(get_db),
):
    service = get_service_by_service_id(
        db,
        service_id,
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found.",
        )

    service.is_active = False

    db.commit()

    return None


@router.get(
    "/{service_id}/health",
    response_model=ServiceHealthResponse,
)
def service_health(
    service_id: str,
    db: Session = Depends(get_db),
):
    service = get_service_by_service_id(
        db,
        service_id,
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found.",
        )

    return {
        "service_id": service.service_id,
        "status": (
            "healthy"
            if service.is_active
            else "inactive"
        ),
        "environment": service.environment,
        "version": service.version,
        "is_active": service.is_active,
    }