from fastapi import FastAPI
from sqlalchemy import text
from app.api import anomalies
from app.api import detection
from app.api import incidents
from app.api import evidence
from app.api import dependencies
from app.api import correlation
from app.api import rca
from app.api import ai_rca
from app.api import remediation
from app.api import approvals
from app.api import recovery
from app.api import chaos
from app.api import slo
from app.api import load_testing
from app.middleware.security import SecurityMiddleware
from app.api import (
    logs,
    metrics,
    services,
    telemetry,
    traces,
)
from app.db import models
from app.db.database import Base, engine


app = FastAPI(
    title="SentinelAI",
    description=(
        "Autonomous Reliability & Root-Cause "
        "Engineering Platform"
    ),
    version="0.4.0",
)


Base.metadata.create_all(bind=engine)


@app.get(
    "/health",
    tags=["System"],
)
def health():
    return {
        "status": "healthy",
        "service": "sentinelai",
        "version": "0.4.0",
    }


@app.get(
    "/health/db",
    tags=["System"],
)
def database_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "postgresql",
    }


app.include_router(services.router)
app.include_router(telemetry.router)
app.include_router(metrics.router)
app.include_router(logs.router)
app.include_router(traces.router)
app.include_router(anomalies.router)
app.include_router(detection.router)
app.include_router(incidents.router)
app.include_router(evidence.router)
app.include_router(dependencies.router)
app.include_router(correlation.router)
app.include_router(rca.router)
app.include_router(ai_rca.router)
app.include_router(remediation.router)
app.include_router(approvals.router)
app.include_router(recovery.router)
app.include_router(chaos.router)
app.include_router(slo.router)
app.include_router(load_testing.router)
app.add_middleware(SecurityMiddleware)