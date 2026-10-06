from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    request_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    trace_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
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
        index=True,
    )

    method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    endpoint: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status_code: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    latency_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    success: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        index=True,
    )

    error_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


Index(
    "ix_telemetry_service_timestamp",
    TelemetryEvent.service_id,
    TelemetryEvent.timestamp,
)

Index(
    "ix_telemetry_status_timestamp",
    TelemetryEvent.status_code,
    TelemetryEvent.timestamp,
)