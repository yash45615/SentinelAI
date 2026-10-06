from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class IncidentEvidence(Base):
    __tablename__ = "incident_evidence"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    incident_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    evidence_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    source_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    service_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="INFO",
    )

    relevance_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    evidence_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        Index(
            "ix_incident_evidence_incident_timestamp",
            "incident_id",
            "evidence_timestamp",
        ),
        Index(
            "ix_incident_evidence_incident_type",
            "incident_id",
            "evidence_type",
        ),
    )