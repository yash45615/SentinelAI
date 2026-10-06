from fastapi.testclient import TestClient

from services.gateway.main import app as gateway_app
from services.orders.main import app as orders_app
from services.payments.main import app as payments_app
from services.inventory.main import app as inventory_app
from services.notifications.main import (
    app as notifications_app,
)


def test_gateway_health():
    client = TestClient(gateway_app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_orders_health():
    client = TestClient(orders_app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "orders-service"


def test_payments_health():
    client = TestClient(payments_app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "payments-service"


def test_inventory_health():
    client = TestClient(inventory_app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "inventory-service"


def test_notifications_health():
    client = TestClient(notifications_app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "notifications-service"


def test_payment_authorization():
    client = TestClient(payments_app)

    response = client.post(
        "/authorize",
        json={
            "amount": 1000,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "authorized"
    assert body["amount"] == 1000
    assert "payment_id" in body
    assert "request_id" in body


def test_inventory_reservation():
    client = TestClient(inventory_app)

    response = client.post(
        "/reserve",
        json={
            "product_id": "product-001",
            "quantity": 2,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "reserved"
    assert body["product_id"] == "product-001"
    assert body["quantity"] == 2


def test_notification():
    client = TestClient(notifications_app)

    response = client.post(
        "/send",
        json={
            "event": "order_created",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "sent"
    assert body["event"] == "order_created"