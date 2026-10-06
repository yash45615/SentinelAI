from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class LoadTestResult(Base):
    __tablename__ = "load_test_results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    test_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    service_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    endpoint: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    concurrency: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    total_requests: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    successful_requests: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    failed_requests: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    requests_per_second: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    p50_latency_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    p95_latency_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    p99_latency_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    error_rate_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    performance_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    gate_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index(
            "ix_load_test_service_created",
            "service_id",
            "created_at",
        ),
        Index(
            "ix_load_test_service_status",
            "service_id",
            "performance_status",
        ),
    )