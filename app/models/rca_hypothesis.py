from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class RcaHypothesis(Base):
    __tablename__ = "rca_hypotheses"

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

    service_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    hypothesis_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SERVICE_FAILURE",
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    anomaly_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    temporal_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    dependency_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    evidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    log_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    trace_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    supporting_evidence_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    contradicting_evidence_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    rank: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        Index(
            "ix_rca_incident_confidence",
            "incident_id",
            "confidence",
        ),
        Index(
            "ix_rca_incident_rank",
            "incident_id",
            "rank",
        ),
    )