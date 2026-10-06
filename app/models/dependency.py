from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ServiceDependency(Base):
    __tablename__ = "service_dependencies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    source_service_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    target_service_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    dependency_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="HTTP",
    )

    criticality: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MEDIUM",
    )

    active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "source_service_id",
            "target_service_id",
            name="uq_service_dependency",
        ),
        Index(
            "ix_dependency_source_target",
            "source_service_id",
            "target_service_id",
        ),
    )