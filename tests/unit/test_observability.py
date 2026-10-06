from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_metric():
    response = client.post(
        "/metrics",
        json={
            "service_id": "orders-service",
            "environment": "production",
            "metric_name": "request_latency_ms",
            "metric_type": "gauge",
            "value": 125.5,
            "unit": "ms",
        },
    )

    assert response.status_code in (200, 201)

    data = response.json()

    assert data["service_id"] == "orders-service"
    assert data["metric_name"] == "request_latency_ms"
    assert data["value"] == 125.5


def test_list_metrics():
    response = client.get("/metrics")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_create_log():
    response = client.post(
        "/logs",
        json={
            "request_id": "req-observability-001",
            "trace_id": "trace-observability-001",
            "service_id": "orders-service",
            "environment": "production",
            "level": "ERROR",
            "event_type": "APPLICATION_ERROR",
            "message": "Payment dependency failed",
            "endpoint": "/orders",
            "status_code": 500,
        },
    )

    assert response.status_code in (200, 201)

    data = response.json()

    assert data["request_id"] == "req-observability-001"
    assert data["trace_id"] == "trace-observability-001"
    assert data["service_id"] == "orders-service"
    assert data["level"] == "ERROR"


def test_list_logs():
    response = client.get("/logs")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_create_trace():
    start = datetime.now(timezone.utc)

    # Use timedelta instead of manually modifying microseconds.
    # This correctly handles crossing a second boundary.
    end = start + timedelta(milliseconds=100)

    response = client.post(
        "/traces",
        json={
            "trace_id": "trace-observability-create-001",
            "span_id": "span-observability-create-001",
            "parent_span_id": None,
            "request_id": "req-observability-create-001",
            "service_id": "orders-service",
            "operation": "create_order",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "duration_ms": 100.0,
            "status_code": 200,
            "status": "OK",
        },
    )

    assert response.status_code in (200, 201)

    data = response.json()

    assert data["trace_id"] == "trace-observability-create-001"
    assert data["span_id"] == "span-observability-create-001"
    assert data["service_id"] == "orders-service"
    assert data["operation"] == "create_order"


def test_get_trace():
    response = client.get(
        "/traces/trace-observability-create-001"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_trace_duplicate_span_id():
    start = datetime.now(timezone.utc)
    end = start + timedelta(milliseconds=50)

    payload = {
        "trace_id": "trace-observability-duplicate-001",
        "span_id": "span-observability-duplicate-001",
        "parent_span_id": None,
        "request_id": "req-observability-duplicate-001",
        "service_id": "orders-service",
        "operation": "duplicate_test",
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "duration_ms": 50.0,
        "status_code": 200,
        "status": "OK",
    }

    first_response = client.post(
        "/traces",
        json=payload,
    )

    assert first_response.status_code in (200, 201)

    second_response = client.post(
        "/traces",
        json=payload,
    )

    assert second_response.status_code == 409


def test_metric_not_found():
    response = client.get("/metrics/999999999")

    assert response.status_code == 404


def test_log_not_found():
    response = client.get("/logs/999999999")

    assert response.status_code == 404