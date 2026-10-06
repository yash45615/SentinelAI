from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# SERVICE SCHEMAS
# ============================================================

class ServiceCreate(BaseModel):
    service_id: str
    name: str
    description: str | None = None
    environment: str = "production"
    version: str = "1.0.0"


class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    environment: str | None = None
    version: str | None = None


class ServiceResponse(BaseModel):
    id: int
    service_id: str
    name: str
    description: str | None
    environment: str
    version: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceHealthResponse(BaseModel):
    service_id: str
    status: str
    environment: str
    version: str
    is_active: bool


# ============================================================
# TELEMETRY SCHEMAS
# ============================================================

class TelemetryCreate(BaseModel):
    request_id: str
    trace_id: str
    service_id: str
    environment: str = "production"
    method: str
    endpoint: str
    status_code: int
    latency_ms: float
    success: bool = True
    error_type: str | None = None
    error_message: str | None = None
    timestamp: datetime | None = None


class TelemetryResponse(BaseModel):
    id: int
    request_id: str
    trace_id: str
    service_id: str
    environment: str
    method: str
    endpoint: str
    status_code: int
    latency_ms: float
    success: bool
    error_type: str | None
    error_message: str | None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# METRIC SCHEMAS
# ============================================================

class MetricCreate(BaseModel):
    service_id: str
    environment: str = "production"
    metric_name: str
    metric_type: str
    value: float
    unit: str | None = None
    timestamp: datetime | None = None


class MetricResponse(BaseModel):
    id: int
    service_id: str
    environment: str
    metric_name: str
    metric_type: str
    value: float
    unit: str | None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# LOG SCHEMAS
# ============================================================

class LogCreate(BaseModel):
    request_id: str | None = None
    trace_id: str | None = None
    service_id: str
    environment: str = "production"
    level: str
    event_type: str
    message: str
    endpoint: str | None = None
    status_code: int | None = None
    timestamp: datetime | None = None


class LogResponse(BaseModel):
    id: int
    request_id: str | None
    trace_id: str | None
    service_id: str
    environment: str
    level: str
    event_type: str
    message: str
    endpoint: str | None
    status_code: int | None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# TRACE SCHEMAS
# ============================================================

class TraceCreate(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    request_id: str | None = None
    service_id: str
    operation: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    status_code: int | None = None
    status: str = "OK"


class TraceResponse(BaseModel):
    id: int
    trace_id: str
    span_id: str
    parent_span_id: str | None
    request_id: str | None
    service_id: str
    operation: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    status_code: int | None
    status: str

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# ANOMALY SCHEMAS
# ============================================================

class AnomalyResponse(BaseModel):
    id: int
    service_id: str
    environment: str
    metric_name: str
    observed_value: float
    baseline_value: float
    deviation_percent: float
    threshold_percent: float
    severity: str
    detection_method: str
    reason: str
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# INCIDENT SCHEMAS
# ============================================================

class IncidentCreate(BaseModel):
    title: str
    description: str | None = None
    service_id: str
    environment: str = "production"
    severity: str = "MEDIUM"
    source: str = "MANUAL"


class IncidentUpdate(BaseModel):
    status: str | None = None
    title: str | None = None
    description: str | None = None
    severity: str | None = None
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )


class IncidentResponse(BaseModel):
    id: int
    incident_key: str
    title: str
    description: str | None
    service_id: str
    environment: str
    severity: str
    status: str
    source: str
    anomaly_id: int | None
    confidence: float | None
    detected_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# INCIDENT TIMELINE SCHEMAS
# ============================================================

class IncidentTimelineEventResponse(BaseModel):
    id: int
    incident_id: int
    event_type: str
    description: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentTimelineResponse(BaseModel):
    incident_id: int
    events: list[IncidentTimelineEventResponse]

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# INCIDENT EVIDENCE SCHEMAS
# ============================================================

class IncidentEvidenceResponse(BaseModel):
    id: int
    incident_id: int
    evidence_type: str
    source_id: str | None
    service_id: str | None
    summary: str
    severity: str | None
    relevance_score: float
    evidence_timestamp: datetime | None
    collected_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# DEPENDENCY SCHEMAS
# ============================================================

class DependencyCreate(BaseModel):
    source_service_id: str
    target_service_id: str
    dependency_type: str = "HTTP"
    criticality: str = "MEDIUM"
    active: bool = True


class DependencyResponse(BaseModel):
    id: int
    source_service_id: str
    target_service_id: str
    dependency_type: str
    criticality: str
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# CORRELATION SCHEMAS
# ============================================================

class CorrelationResponse(BaseModel):
    service_id: str
    relationship: str
    correlation_score: float
    temporal_score: float
    dependency_score: float
    explanation: str


# ============================================================
# RCA SCHEMAS
# ============================================================

class RcaHypothesisResponse(BaseModel):
    id: int
    incident_id: int
    service_id: str
    hypothesis_type: str
    title: str
    explanation: str
    confidence: float

    anomaly_score: float
    temporal_score: float
    dependency_score: float
    evidence_score: float
    log_score: float
    trace_score: float

    supporting_evidence_count: int
    contradicting_evidence_count: int
    rank: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AiRcaAnalysisResponse(BaseModel):
    id: int
    incident_id: int
    selected_hypothesis_id: int | None
    provider: str
    model: str
    summary: str
    root_cause: str
    reasoning: str
    recommended_action: str
    confidence: float
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RemediationActionCreate(BaseModel):
    service_id: str
    action_type: str
    reason: str


class RemediationActionResponse(BaseModel):
    id: int
    incident_id: int
    service_id: str
    action_type: str
    reason: str
    status: str
    result: str | None
    requested_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    rollback_available: bool
    rollback_action: str | None

    model_config = ConfigDict(from_attributes=True)

class ApprovalRequestCreate(BaseModel):
    requested_by: str = "sentinelai"


class ApprovalDecision(BaseModel):
    decided_by: str
    decision_reason: str


class RemediationApprovalResponse(BaseModel):
    id: int
    remediation_action_id: int
    incident_id: int
    requested_by: str
    approved_by: str | None
    status: str
    reason: str
    decision_reason: str | None
    expires_at: datetime
    created_at: datetime
    decided_at: datetime | None
    is_valid: bool

    model_config = ConfigDict(from_attributes=True)

class RecoveryCheckResponse(BaseModel):
    id: int
    incident_id: int
    remediation_action_id: int | None
    service_id: str
    check_type: str
    expected_value: float | None
    observed_value: float | None
    status: str
    details: str
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecoveryVerificationResponse(BaseModel):
    incident_id: int
    remediation_action_id: int | None
    overall_status: str
    checks: list[RecoveryCheckResponse]

class ChaosExperimentCreate(BaseModel):
    target_service_id: str
    failure_type: str
    intensity: float = Field(
        default=1.0,
        gt=0,
        le=10,
    )
    duration_seconds: int = Field(
        default=30,
        gt=0,
        le=300,
    )


class ChaosExperimentResponse(BaseModel):
    id: int
    experiment_id: str
    incident_id: int | None
    target_service_id: str
    failure_type: str
    intensity: float
    duration_seconds: int
    status: str
    expected_effect: str
    actual_effect: str | None
    incident_created: bool
    recovery_time_seconds: float | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChaosStartResponse(BaseModel):
    experiment_id: str
    status: str
    failure_type: str
    target_service_id: str
    actual_effect: str

class SloResultResponse(BaseModel):
    id: int
    service_id: str
    environment: str
    window_minutes: int

    availability_target: float
    availability_actual: float

    error_rate_target: float
    error_rate_actual: float

    p95_latency_target_ms: float
    p95_latency_actual_ms: float

    detection_target_seconds: float
    detection_actual_seconds: float | None

    recovery_target_seconds: float
    recovery_actual_seconds: float | None

    availability_met: bool
    error_rate_met: bool
    latency_met: bool
    detection_met: bool | None
    recovery_met: bool | None

    overall_status: str

    error_budget_percent: float
    error_budget_remaining_percent: float
    burn_rate: float

    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LoadTestRequest(BaseModel):
    base_url: str
    service_id: str
    endpoint: str = "/health"
    concurrency: int = Field(
        default=5,
        gt=0,
        le=100,
    )
    duration_seconds: int = Field(
        default=10,
        gt=0,
        le=300,
    )


class LoadTestResultResponse(BaseModel):
    id: int
    test_id: str
    service_id: str
    endpoint: str
    concurrency: int
    duration_seconds: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate_percent: float
    performance_status: str
    gate_reason: str
    started_at: datetime
    completed_at: datetime
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )