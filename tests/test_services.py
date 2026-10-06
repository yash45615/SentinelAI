from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def unique_service_id(prefix: str = "test-service") -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def test_create_service():
    service_id = unique_service_id()

    payload = {
        "service_id": service_id,
        "name": "Orders Service",
        "description": "Test order processing service",
        "environment": "test",
        "version": "1.0.0",
    }

    response = client.post(
        "/services",
        json=payload,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["service_id"] == service_id
    assert body["name"] == "Orders Service"
    assert body["environment"] == "test"
    assert body["version"] == "1.0.0"
    assert body["is_active"] is True


def test_duplicate_service_rejected():
    service_id = unique_service_id()

    payload = {
        "service_id": service_id,
        "name": "Duplicate Test Service",
        "environment": "test",
        "version": "1.0.0",
    }

    first = client.post(
        "/services",
        json=payload,
    )

    second = client.post(
        "/services",
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_get_service():
    service_id = unique_service_id()

    payload = {
        "service_id": service_id,
        "name": "Get Test Service",
        "environment": "test",
        "version": "2.0.0",
    }

    create_response = client.post(
        "/services",
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/services/{service_id}"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["service_id"] == service_id
    assert body["name"] == "Get Test Service"
    assert body["version"] == "2.0.0"


def test_get_missing_service():
    response = client.get(
        "/services/does-not-exist"
    )

    assert response.status_code == 404


def test_update_service():
    service_id = unique_service_id()

    payload = {
        "service_id": service_id,
        "name": "Original Service",
        "environment": "test",
        "version": "1.0.0",
    }

    create_response = client.post(
        "/services",
        json=payload,
    )

    assert create_response.status_code == 201

    update_response = client.patch(
        f"/services/{service_id}",
        json={
            "name": "Updated Service",
            "version": "2.0.0",
        },
    )

    assert update_response.status_code == 200

    body = update_response.json()

    assert body["name"] == "Updated Service"
    assert body["version"] == "2.0.0"
    assert body["environment"] == "test"


def test_list_service_filter():
    service_id = unique_service_id()

    payload = {
        "service_id": service_id,
        "name": "Production Orders",
        "environment": "production",
        "version": "1.0.0",
    }

    create_response = client.post(
        "/services",
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.get(
        "/services",
        params={
            "environment": "production",
            "active_only": "true",
        },
    )

    assert response.status_code == 200

    services = response.json()

    assert isinstance(services, list)

    assert any(
        service["service_id"] == service_id
        for service in services
    )


def test_search_services():
    service_id = unique_service_id()

    payload = {
        "service_id": service_id,
        "name": "Payment Processing Service",
        "environment": "test",
        "version": "1.0.0",
    }

    create_response = client.post(
        "/services",
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.get(
        "/services",
        params={
            "search": "Payment Processing"
        },
    )

    assert response.status_code == 200

    services = response.json()

    assert any(
        service["service_id"] == service_id
        for service in services
    )


def test_service_health():
    service_id = unique_service_id()

    payload = {
        "service_id": service_id,
        "name": "Health Test Service",
        "environment": "test",
        "version": "1.0.0",
    }

    create_response = client.post(
        "/services",
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/services/{service_id}/health"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["service_id"] == service_id
    assert body["status"] == "healthy"
    assert body["is_active"] is True


def test_deactivate_service():
    service_id = unique_service_id()

    payload = {
        "service_id": service_id,
        "name": "Deactivate Test Service",
        "environment": "test",
        "version": "1.0.0",
    }

    create_response = client.post(
        "/services",
        json=payload,
    )

    assert create_response.status_code == 201

    delete_response = client.delete(
        f"/services/{service_id}"
    )

    assert delete_response.status_code == 204

    health_response = client.get(
        f"/services/{service_id}/health"
    )

    assert health_response.status_code == 200

    body = health_response.json()

    assert body["status"] == "inactive"
    assert body["is_active"] is False