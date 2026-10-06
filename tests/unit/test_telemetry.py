from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_telemetry():
    response = client.post(
        "/telemetry",
        json={
            "request_id": "req-unit-001",
            "trace_id": "trace-unit-001",
            "service_id": "payments-service",
            "environment": "production",
            "method": "POST",
            "endpoint": "/authorize",
            "status_code": 200,
            "latency_ms": 25.5,
            "success": True,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["request_id"] == "req-unit-001"
    assert body["trace_id"] == "trace-unit-001"
    assert body["service_id"] == "payments-service"
    assert body["status_code"] == 200
    assert body["success"] is True


def test_list_telemetry():
    response = client.get(
        "/telemetry?service_id=payments-service"
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)