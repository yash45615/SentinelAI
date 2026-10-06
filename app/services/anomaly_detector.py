from dataclasses import dataclass


@dataclass
class DetectionResult:
    is_anomaly: bool
    severity: str
    deviation_percent: float
    reason: str


class AnomalyDetector:
    """
    Deterministic anomaly detector.

    The detector compares an observed metric value against
    a baseline value and classifies the anomaly based on
    percentage deviation.
    """

    def detect(
        self,
        metric_name: str,
        baseline_value: float,
        observed_value: float,
        threshold_percent: float = 50.0,
    ) -> DetectionResult:

        if baseline_value <= 0:
            raise ValueError("Baseline value must be greater than zero.")

        deviation_percent = (
            abs(observed_value - baseline_value)
            / baseline_value
        ) * 100

        if deviation_percent < threshold_percent:
            return DetectionResult(
                is_anomaly=False,
                severity="INFO",
                deviation_percent=deviation_percent,
                reason=(
                    f"{metric_name} is within the configured "
                    f"threshold of {threshold_percent:.2f}%."
                ),
            )

        ratio = deviation_percent / threshold_percent

        if ratio >= 4:
            severity = "CRITICAL"
        elif ratio >= 2.5:
            severity = "HIGH"
        elif ratio >= 1.5:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        direction = "increased" if observed_value > baseline_value else "decreased"

        reason = (
            f"{metric_name} {direction} by "
            f"{deviation_percent:.2f}% compared with the baseline."
        )

        return DetectionResult(
            is_anomaly=True,
            severity=severity,
            deviation_percent=deviation_percent,
            reason=reason,
        )


detector = AnomalyDetector()