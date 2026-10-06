from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class RecoveryCheck(Base):
    __tablename__ = "recovery_checks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    incident_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    remediation_action_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    service_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    check_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    expected_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    observed_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    details: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index(
            "ix_recovery_incident_checked",
            "incident_id",
            "checked_at",
        ),
        Index(
            "ix_recovery_incident_status",
            "incident_id",
            "status",
        ),
    )