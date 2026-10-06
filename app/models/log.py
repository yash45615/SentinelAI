from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class LogEvent(Base):
    __tablename__ = "log_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    request_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    trace_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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

    level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    endpoint: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


Index(
    "ix_log_service_timestamp",
    LogEvent.service_id,
    LogEvent.timestamp,
)

Index(
    "ix_log_level_timestamp",
    LogEvent.level,
    LogEvent.timestamp,
)