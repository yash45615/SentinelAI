from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    service_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    environment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="production",
        index=True,
    )

    metric_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    observed_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    baseline_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    deviation_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    threshold_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    detection_method: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="threshold",
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    __table_args__ = (
        Index(
            "ix_anomalies_service_metric_detected",
            "service_id",
            "metric_name",
            "detected_at",
        ),
    )