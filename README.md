# SentinelAI

### Autonomous Reliability & Root-Cause Engineering Platform

SentinelAI is a production-inspired reliability engineering platform that detects incidents, correlates distributed-system evidence, generates explainable root-cause hypotheses, recommends controlled remediation, verifies recovery, and continuously evaluates service reliability.

The platform simulates a distributed production environment containing an API Gateway, Orders, Payments, Inventory, and Notifications services.

Instead of treating monitoring as a collection of dashboards, SentinelAI models the complete incident lifecycle:

**Telemetry → Detection → Incident → Evidence → Correlation → RCA → Confidence Scoring → Remediation → Approval → Recovery Verification**

---

## Why SentinelAI?

Modern distributed systems can fail in ways that are difficult to diagnose:

* A payment service becomes slow.
* Orders begin timing out several seconds later.
* Error rates increase across dependent services.
* A deployment happened immediately before the degradation.
* A queue starts accumulating work.
* Multiple services report symptoms, but only one is the likely root cause.

SentinelAI is designed to answer:

> **What failed, why did it fail, what evidence supports the diagnosis, what should be done, and did the system actually recover?**

The platform combines observability, deterministic reasoning, reliability engineering, controlled automation, and AI-assisted analysis into one workflow.

---

## Architecture

```text
                         ┌──────────────────────┐
                         │   Synthetic Users    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     API Gateway      │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
       │    Orders   │──────▶│  Payments   │       │  Inventory  │
       │   Service   │       │   Service   │       │   Service   │
       └──────┬──────┘       └─────────────┘       └─────────────┘
              │
              ▼
       ┌─────────────┐
       │Notifications│
       │   Service   │
       └─────────────┘


                    SentinelAI Control Plane
                    ========================

       ┌─────────────────────────────────────────┐
       │            Telemetry Layer              │
       │ Metrics │ Logs │ Traces │ Requests       │
       └───────────────────┬─────────────────────┘
                           │
                           ▼
       ┌─────────────────────────────────────────┐
       │         Anomaly Detection Engine        │
       └───────────────────┬─────────────────────┘
                           │
                           ▼
       ┌─────────────────────────────────────────┐
       │          Incident Management            │
       │ Detection │ Timeline │ Lifecycle         │
       └───────────────────┬─────────────────────┘
                           │
                           ▼
       ┌─────────────────────────────────────────┐
       │          Evidence Collection             │
       │ Metrics │ Logs │ Traces │ Anomalies      │
       └───────────────────┬─────────────────────┘
                           │
                           ▼
       ┌─────────────────────────────────────────┐
       │        Dependency Correlation            │
       │ Temporal │ Dependency │ Blast Radius     │
       └───────────────────┬─────────────────────┘
                           │
                           ▼
       ┌─────────────────────────────────────────┐
       │              RCA Engine                  │
       │ Candidate Generation + Scoring           │
       └───────────────────┬─────────────────────┘
                           │
                           ▼
       ┌─────────────────────────────────────────┐
       │       Explainable Confidence             │
       │ Anomaly │ Temporal │ Evidence │ Logs     │
       │ Dependency │ Traces                      │
       └───────────────────┬─────────────────────┘
                           │
                           ▼
       ┌─────────────────────────────────────────┐
       │         AI-Assisted RCA                  │
       │ Deterministic fallback + optional LLM    │
       └───────────────────┬─────────────────────┘
                           │
                           ▼
       ┌─────────────────────────────────────────┐
       │          Remediation Engine              │
       │ Restart │ Rollback │ Traffic │ Queue     │
       └───────────────────┬─────────────────────┘
                           │
                           ▼
       ┌─────────────────────────────────────────┐
       │        Human Approval Gateway             │
       │ Authorization │ TTL │ Safety Gates        │
       └───────────────────┬─────────────────────┘
                           │
                           ▼
       ┌─────────────────────────────────────────┐
       │         Recovery Verification             │
       │ Latency │ Errors │ Queue │ Dependencies   │
       └───────────────────┬─────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Incident Closed │
                  └─────────────────┘
```

---

# Core Capabilities

## 1. Service Registry

Register and manage production services with:

* Service identity
* Environment
* Version
* Description
* Active/inactive state
* Service health

### API

```text
POST   /services
GET    /services
GET    /services/{service_id}
PATCH  /services/{service_id}
DELETE /services/{service_id}
GET    /services/{service_id}/health
```

---

# 2. Synthetic Distributed Production Environment

SentinelAI includes multiple independent services:

| Service       | Port | Responsibility        |
| ------------- | ---: | --------------------- |
| API Gateway   | 8100 | Request routing       |
| Orders        | 8101 | Order processing      |
| Payments      | 8102 | Payment processing    |
| Inventory     | 8103 | Inventory management  |
| Notifications | 8104 | Notification delivery |

The services communicate over HTTP and propagate:

* Request IDs
* Trace IDs
* Latency
* Status codes
* Error information

Failure injection can be used to reproduce realistic distributed incidents.

---

# 3. Observability

SentinelAI collects three major observability signals:

### Metrics

Examples:

```text
request_latency_ms
request_count
error_rate
queue_depth
cpu_usage
```

### Logs

Structured events containing:

```text
request_id
trace_id
service_id
event_type
level
message
status_code
timestamp
```

### Traces

Distributed request information containing:

```text
trace_id
span_id
parent_span_id
service_id
operation
start_time
end_time
duration
status
```

These signals become the evidence base for automated incident investigation.

---

# 4. Anomaly Detection

The detection engine compares observed values against baselines.

Example:

```text
Baseline latency:    100 ms
Observed latency:    420 ms
Deviation:           320%
Threshold:           50%
```

The engine classifies anomalies according to severity:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Each anomaly contains an explanation and detection metadata.

---

# 5. Incident Management

Incidents have an explicit lifecycle.

```text
DETECTED
   ↓
TRIAGED
   ↓
INVESTIGATING
   ↓
ROOT_CAUSE_IDENTIFIED
   ↓
REMEDIATION_PENDING
   ↓
REMEDIATING
   ↓
VERIFYING
   ↓
RESOLVED
```

Failure states include:

```text
FAILED
CANCELLED
```

Invalid lifecycle transitions are rejected.

Every important transition is recorded in the incident timeline.

---

# 6. Evidence Collection

When an incident is created, SentinelAI can collect surrounding evidence from a configurable time window.

Evidence sources include:

* Metrics
* Logs
* Traces
* Anomalies
* Service metadata

Evidence is associated with:

```text
incident
service
source
timestamp
severity
relevance score
```

This allows the RCA engine to reason over evidence instead of relying on a single signal.

---

# 7. Dependency-Aware Correlation

SentinelAI maintains a service dependency graph.

Example:

```text
API Gateway
     │
     ▼
  Orders
   ├──────▶ Payments
   ├──────▶ Inventory
   └──────▶ Notifications
```

Correlation considers:

### Temporal correlation

Did the suspected service degrade before the incident?

### Dependency correlation

Is the suspected service actually upstream/downstream of the affected service?

### Severity / criticality

How important is the dependency?

### Combined correlation score

```text
Correlation Score =
    Temporal Score × 0.60
  + Dependency Score × 0.40
```

---

# 8. Deterministic RCA Engine

The RCA engine generates multiple candidate root causes instead of returning a single unexplained answer.

Each candidate is scored using:

```text
Anomaly
Temporal correlation
Dependency relationship
Evidence relevance
Log failures
Trace failures
```

The final confidence score is:

```text
Confidence =
    anomaly      × 0.30
  + temporal     × 0.20
  + dependency   × 0.20
  + evidence     × 0.15
  + logs         × 0.10
  + traces       × 0.05
```

Example output:

```text
Incident: INC-1042

Affected Service:
orders-service

Probable Root Cause:
payments-service latency regression

Confidence:
0.87

Supporting Evidence:
- Payment latency increased significantly
- Payment errors increased
- Orders degraded shortly afterward
- Orders depends on Payments
- Payment deployment preceded the anomaly

Recommended Action:
Rollback payment deployment
```

The important design principle is:

> **Every RCA result should be explainable.**

---

# 9. Explainable Confidence Scoring

Instead of returning:

```text
Root cause: Payments
Confidence: 87%
```

SentinelAI exposes the underlying reasoning:

```text
Anomaly score:       0.92
Temporal score:      0.94
Dependency score:    0.90
Evidence score:      0.86
Log score:           0.80
Trace score:         0.75
```

This makes the RCA process auditable and easier to debug.

---

# 10. AI-Assisted RCA

SentinelAI supports optional AI-assisted analysis.

The AI layer receives structured incident context including:

* Incident information
* Ranked RCA hypotheses
* Evidence
* Service relationships
* Confidence scores

It produces structured output containing:

```text
Summary
Root Cause
Reasoning
Recommended Action
Confidence
```

AI RCA is **optional**.

When AI is disabled or unavailable, SentinelAI falls back to the deterministic RCA engine.

This means the core reliability workflow does not depend on an external LLM API.

---

# 11. Remediation Engine

The remediation engine supports controlled synthetic actions:

```text
RESTART_SERVICE
ROLLBACK_DEPLOYMENT
PAUSE_TRAFFIC
REDUCE_CONCURRENCY
CLEAR_QUEUE
SWITCH_DEPENDENCY
```

The workflow is:

```text
RCA
 ↓
Recommendation
 ↓
Remediation Request
 ↓
Approval
 ↓
Execution
 ↓
Recovery Verification
```

Actions are tracked throughout their lifecycle.

---

# 12. Human Approval & Safety Gates

SentinelAI does not blindly execute potentially destructive actions.

Sensitive remediation operations require approval.

Approval states:

```text
PENDING
APPROVED
REJECTED
EXPIRED
```

Approval requests also support:

* Requester identity
* Approver identity
* Decision reason
* Expiration
* Validity checking
* Decision timestamp

This provides a safety boundary between automated diagnosis and automated action.

---

# 13. Recovery Verification

After remediation, SentinelAI verifies whether the system actually recovered.

Checks include:

```text
Service health
Latency
Error rate
Queue backlog
Dependency health
```

Possible outcomes:

```text
PASS
FAIL
INCONCLUSIVE
```

A successful verification can automatically transition:

```text
VERIFYING → RESOLVED
```

A failed verification can trigger further remediation or escalation.

---

# 14. Chaos Engineering

SentinelAI includes controlled failure scenarios:

```text
LATENCY_INJECTION
SERVICE_CRASH
DB_SLOWDOWN
CPU_STRESS
MEMORY_PRESSURE
QUEUE_BACKLOG
DEPENDENCY_FAILURE
BAD_DEPLOYMENT
```

Each experiment records:

```text
Experiment ID
Target Service
Failure Type
Intensity
Duration
Expected Effect
Actual Effect
Incident Created
Recovery Time
Start Time
Completion Time
```

This allows the platform itself to be tested against realistic failure conditions.

---

# 15. SLO & Reliability Analytics

SentinelAI evaluates reliability against configurable targets.

Default targets:

| SLO                   |   Target |
| --------------------- | -------: |
| Availability          |  ≥ 99.9% |
| Error Rate            |     < 1% |
| P95 Latency           | < 500 ms |
| Incident Detection    | < 30 sec |
| Recovery Verification | < 60 sec |

The SLO engine calculates:

* Availability
* Error rate
* P95 latency
* Detection time
* Recovery time
* Error budget
* Error-budget remaining
* Burn rate
* Overall reliability status

---

# 16. Load Testing & Reliability Gates

SentinelAI includes an asynchronous HTTP load-testing engine.

It measures:

```text
Total requests
Successful requests
Failed requests
Requests/second
P50 latency
P95 latency
P99 latency
Error rate
```

Default reliability gates include:

```text
P95 latency < 500 ms
Error rate < 1%
```

Performance results are persisted so they can be compared over time.

---

# 17. Security & Production Hardening

The platform includes:

* Environment-based configuration
* API-key protected administrative operations
* CORS allowlisting
* Request IDs
* Rate limiting
* Security response headers
* Audit logging
* Configurable API documentation
* Environment separation
* Secret protection through `.env`
* No credentials committed to Git

Sensitive operations are explicitly protected rather than exposed as unrestricted endpoints.

---

# 18. Audit Logging

Security-sensitive operations can be recorded with:

```text
Request ID
Actor
Action
Resource Type
Resource ID
Outcome
Details
Timestamp
```

This provides an audit trail for operational actions.

---

# Technology Stack

### Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* Pydantic Settings

### Database

* PostgreSQL

### Caching / Infrastructure

* Redis-compatible infrastructure

### Testing

* Pytest
* HTTPX

### Reliability

* Metrics
* Logs
* Distributed traces
* Anomaly detection
* RCA
* SLOs
* Load testing
* Chaos engineering

### AI

* Optional OpenAI-compatible LLM integration
* Deterministic fallback

### CI/CD

* GitHub Actions
* Automated test matrix
* Reliability gates
* Coverage reporting

---

# Project Structure

```text
SentinelAI/
│
├── app/
│   ├── api/
│   │   ├── approvals.py
│   │   ├── anomalies.py
│   │   ├── chaos.py
│   │   ├── correlation.py
│   │   ├── dependencies.py
│   │   ├── evidence.py
│   │   ├── incidents.py
│   │   ├── load_tests.py
│   │   ├── logs.py
│   │   ├── metrics.py
│   │   ├── rca.py
│   │   ├── remediation.py
│   │   ├── recovery.py
│   │   ├── services.py
│   │   ├── slo.py
│   │   ├── telemetry.py
│   │   └── traces.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── models.py
│   │
│   ├── middleware/
│   │   └── security.py
│   │
│   ├── models/
│   │   ├── ai_rca_analysis.py
│   │   ├── anomaly.py
│   │   ├── audit_log.py
│   │   ├── chaos_experiment.py
│   │   ├── dependency.py
│   │   ├── incident.py
│   │   ├── incident_evidence.py
│   │   ├── incident_timeline.py
│   │   ├── load_test_result.py
│   │   ├── log.py
│   │   ├── metric.py
│   │   ├── rca_hypothesis.py
│   │   ├── recovery_check.py
│   │   ├── remediation_action.py
│   │   ├── remediation_approval.py
│   │   ├── service.py
│   │   ├── slo_result.py
│   │   ├── telemetry.py
│   │   └── trace.py
│   │
│   ├── services/
│   │   ├── ai_rca_assistant.py
│   │   ├── anomaly_detector.py
│   │   ├── approval_gateway.py
│   │   ├── audit_service.py
│   │   ├── chaos_engine.py
│   │   ├── correlation_engine.py
│   │   ├── evidence_collector.py
│   │   ├── incident_manager.py
│   │   ├── load_test_engine.py
│   │   ├── rca_engine.py
│   │   ├── recovery_verifier.py
│   │   ├── remediation_engine.py
│   │   ├── slo_engine.py
│   │   └── timeline_builder.py
│   │
│   └── main.py
│
├── services/
│   ├── gateway/
│   ├── orders/
│   ├── payments/
│   ├── inventory/
│   └── notifications/
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── reliability.yml
│
├── .env.example
├── .gitignore
├── requirements.txt
├── run_tests.ps1
└── README.md
```

---

# Running Locally

## 1. Clone the repository

```powershell
git clone https://github.com/<your-username>/SentinelAI.git
cd SentinelAI
```

## 2. Create a virtual environment

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure environment

Create `.env` from `.env.example`.

Example:

```env
APP_ENV=development

DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/sentinelai_db

CORS_ORIGINS=http://localhost:5173

AI_RCA_ENABLED=false
AI_RCA_PROVIDER=openai
AI_RCA_MODEL=gpt-4.1-mini
AI_RCA_API_KEY=
AI_RCA_TIMEOUT_SECONDS=30

SECURITY_ENABLED=false
ADMIN_API_KEY=change-this-in-production

RATE_LIMIT_ENABLED=false
RATE_LIMIT_REQUESTS=120
RATE_LIMIT_WINDOW_SECONDS=60

DOCS_ENABLED=true
```

Never commit the real `.env` file.

---

# Database Initialization

Create the PostgreSQL database:

```sql
CREATE DATABASE sentinelai_db;
```

Then initialize the tables:

```powershell
python -c "from app.db.database import Base, engine; import app.db.models; Base.metadata.create_all(bind=engine); print('SentinelAI database initialized.')"
```

---

# Start SentinelAI

```powershell
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Start Synthetic Services

### Gateway

```powershell
uvicorn services.gateway.main:app --port 8100
```

### Orders

```powershell
uvicorn services.orders.main:app --port 8101
```

### Payments

```powershell
uvicorn services.payments.main:app --port 8102
```

### Inventory

```powershell
uvicorn services.inventory.main:app --port 8103
```

### Notifications

```powershell
uvicorn services.notifications.main:app --port 8104
```

---

# Running Tests

Run the complete test suite:

```powershell
pytest -q
```

Or use the reliability gate:

```powershell
.\run_tests.ps1
```

The local reliability gate validates:

```text
Full test suite
RCA engine
Recovery verification
Chaos engineering
SLO engine
Load testing
Security
Security middleware
```

---

# CI/CD

GitHub Actions automatically validates the project.

## SentinelAI CI

The CI pipeline:

* Tests Python 3.10
* Tests Python 3.11
* Tests Python 3.12
* Starts PostgreSQL
* Creates the CI database
* Runs the complete test suite
* Generates coverage
* Uploads coverage artifacts

## Reliability Gate

The reliability workflow validates:

* Application imports
* RCA engine
* Recovery verification
* Chaos engineering
* SLO calculations
* Load testing
* Security
* Security middleware

A pull request should not be considered healthy until the reliability checks pass.

---

# Example Incident Investigation

Consider the following failure:

```text
Payment Service
    ↓
Latency increases from 120 ms → 650 ms
    ↓
Anomaly detected
    ↓
Incident created
    ↓
Orders begins returning errors
```

SentinelAI collects:

```text
Metrics
Logs
Traces
Anomalies
Dependencies
Incident timeline
```

The RCA engine evaluates candidates:

```text
Candidate 1
Payment Service latency regression
Confidence: 0.87

Candidate 2
Orders Service internal failure
Confidence: 0.54

Candidate 3
Inventory Service anomaly
Confidence: 0.21
```

The system explains why the first hypothesis ranked highest.

It can then recommend:

```text
ROLLBACK_DEPLOYMENT
```

The action enters:

```text
REMEDIATION_PENDING
```

A human approves it.

The remediation executes.

SentinelAI then verifies:

```text
Latency       PASS
Error Rate    PASS
Dependencies  PASS
Service Health PASS
```

The incident transitions:

```text
VERIFYING → RESOLVED
```

---

# Design Principles

### Explainability over black-box decisions

Every RCA hypothesis exposes its scoring dimensions and supporting evidence.

### Automation with safety boundaries

Diagnosis can be automated, but destructive remediation requires explicit authorization.

### Deterministic first, AI second

The reliability workflow remains functional without an external AI provider.

### Evidence-driven RCA

Root-cause decisions are based on multiple telemetry signals rather than a single metric.

### Failure-aware design

The system assumes that distributed systems fail and makes those failures testable.

### Reliability as a measurable property

SLOs, error budgets, latency gates, recovery times, and load tests turn reliability into measurable engineering outcomes.

---

# Reliability Workflow

```text
┌──────────────┐
│  Telemetry   │
└──────┬───────┘
       ↓
┌──────────────┐
│   Anomaly    │
│  Detection   │
└──────┬───────┘
       ↓
┌──────────────┐
│   Incident   │
│  Management  │
└──────┬───────┘
       ↓
┌──────────────┐
│   Evidence   │
│  Collection  │
└──────┬───────┘
       ↓
┌──────────────┐
│ Dependency + │
│   Timeline   │
│ Correlation  │
└──────┬───────┘
       ↓
┌──────────────┐
│     RCA      │
└──────┬───────┘
       ↓
┌──────────────┐
│  Confidence  │
│   Scoring    │
└──────┬───────┘
       ↓
┌──────────────┐
│ AI-Assisted  │
│     RCA      │
└──────┬───────┘
       ↓
┌──────────────┐
│ Remediation  │
└──────┬───────┘
       ↓
┌──────────────┐
│   Approval   │
│    Gate      │
└──────┬───────┘
       ↓
┌──────────────┐
│   Recovery   │
│ Verification │
└──────┬───────┘
       ↓
┌──────────────┐
│   RESOLVED   │
└──────────────┘
```

---

# What This Project Demonstrates

SentinelAI demonstrates practical experience with:

* Distributed systems
* Backend engineering
* FastAPI
* PostgreSQL
* SQLAlchemy
* REST APIs
* Service dependencies
* Observability
* Metrics, logs, and traces
* Anomaly detection
* Incident management
* Root-cause analysis
* Explainable scoring
* AI-assisted engineering
* Safe automation
* Human-in-the-loop workflows
* Recovery verification
* Chaos engineering
* SLO engineering
* Error budgets
* Load testing
* Performance gates
* Security hardening
* Audit logging
* CI/CD
* Automated reliability validation

---

# Project Status

| Capability                     | Status |
| ------------------------------ | ------ |
| Service Registry               | ✅      |
| Synthetic Production Services  | ✅      |
| Telemetry Collection           | ✅      |
| Metrics                        | ✅      |
| Logs                           | ✅      |
| Distributed Traces             | ✅      |
| Anomaly Detection              | ✅      |
| Incident Management            | ✅      |
| Evidence Collection            | ✅      |
| Dependency Correlation         | ✅      |
| Timeline Reconstruction        | ✅      |
| Deterministic RCA              | ✅      |
| Explainable Confidence Scoring | ✅      |
| AI-Assisted RCA                | ✅      |
| Remediation Engine             | ✅      |
| Human Approval Gateway         | ✅      |
| Recovery Verification          | ✅      |
| Chaos Engineering              | ✅      |
| SLO Analytics                  | ✅      |
| Load Testing                   | ✅      |
| Security Hardening             | ✅      |
| Audit Logging                  | ✅      |
| CI/CD                          | ✅      |
| Reliability Gates              | ✅      |

---

# Future Enhancements

Potential extensions include:

* OpenTelemetry SDK integration
* Prometheus metrics ingestion
* Grafana dashboards
* Real-time incident streaming
* Kafka-based event ingestion
* Kubernetes deployment
* Distributed rate limiting
* Persistent job queues
* ML-based anomaly detection
* Advanced dependency graphs
* Historical RCA learning
* Automated canary analysis
* Deployment risk scoring
* Multi-region reliability analysis

---

# Author

**Yash Kalbhile**

Built as a production-inspired reliability engineering platform demonstrating backend engineering, distributed systems, observability, automated RCA, safe remediation, and AI-assisted operations.

---

## License

This project is intended for educational, portfolio, and engineering demonstration purposes.
