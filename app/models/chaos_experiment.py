from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, Float, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ChaosExperiment(Base):
    __tablename__ = "chaos_experiments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    experiment_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    incident_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    target_service_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    failure_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    intensity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PLANNED",
        index=True,
    )

    expected_effect: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    actual_effect: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    incident_created: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    recovery_time_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index(
            "ix_chaos_target_created",
            "target_service_id",
            "created_at",
        ),
        Index(
            "ix_chaos_failure_status",
            "failure_type",
            "status",
        ),
    )