from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SloResult(Base):
    __tablename__ = "slo_results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    service_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    environment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="production",
    )

    window_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
    )

    availability_target: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=99.9,
    )

    availability_actual: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    error_rate_target: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    error_rate_actual: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    p95_latency_target_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=500.0,
    )

    p95_latency_actual_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    detection_target_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=30.0,
    )

    detection_actual_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    recovery_target_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=60.0,
    )

    recovery_actual_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    availability_met: Mapped[bool] = mapped_column(
        nullable=False,
    )

    error_rate_met: Mapped[bool] = mapped_column(
        nullable=False,
    )

    latency_met: Mapped[bool] = mapped_column(
        nullable=False,
    )

    detection_met: Mapped[bool | None] = mapped_column(
        nullable=True,
    )

    recovery_met: Mapped[bool | None] = mapped_column(
        nullable=True,
    )

    overall_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    error_budget_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    error_budget_remaining_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    burn_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index(
            "ix_slo_service_calculated",
            "service_id",
            "calculated_at",
        ),
        Index(
            "ix_slo_service_status",
            "service_id",
            "overall_status",
        ),
    )