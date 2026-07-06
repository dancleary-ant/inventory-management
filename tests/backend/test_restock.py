"""
Tests for the restocking order endpoints (POST /api/orders/restock, GET /api/orders/submitted).
"""
import pytest


@pytest.fixture
def restock_payload():
    """A valid restock order request. TMP-201 is a Sensors item (10-day lead time)."""
    return {
        "items": [
            {"sku": "TMP-201", "name": "Temperature Sensor Module", "quantity": 10, "unit_cost": 89.5}
        ],
        "budget": 1000.0,
    }


def test_create_restock_order(client, restock_payload):
    response = client.post("/api/orders/restock", json=restock_payload)
    assert response.status_code == 201
    order = response.json()
    assert order["order_number"].startswith("RST-")
    assert order["status"] == "Submitted"
    assert order["total_value"] == 895.0
    assert order["lead_time_days"] == 10  # Sensors category constant
    assert order["expected_delivery"] > order["order_date"]
    assert len(order["items"]) == 1


def test_submitted_order_appears_in_list(client, restock_payload):
    created = client.post("/api/orders/restock", json=restock_payload).json()
    response = client.get("/api/orders/submitted")
    assert response.status_code == 200
    assert any(o["id"] == created["id"] for o in response.json())


def test_empty_items_rejected(client):
    response = client.post("/api/orders/restock", json={"items": [], "budget": 500.0})
    assert response.status_code == 400


def test_over_budget_rejected(client, restock_payload):
    restock_payload["budget"] = 10.0
    response = client.post("/api/orders/restock", json=restock_payload)
    assert response.status_code == 400
    assert "exceeds budget" in response.json()["detail"]


def test_unknown_sku_uses_default_lead_time(client):
    payload = {
        "items": [{"sku": "ZZZ-999", "name": "Mystery Part", "quantity": 1, "unit_cost": 5.0}],
        "budget": 100.0,
    }
    response = client.post("/api/orders/restock", json=payload)
    assert response.status_code == 201
    assert response.json()["lead_time_days"] == 7


def test_lead_time_is_max_across_items(client):
    # Sensors (10) + Controllers (15) -> order lead time 15
    payload = {
        "items": [
            {"sku": "TMP-201", "name": "Temperature Sensor Module", "quantity": 1, "unit_cost": 89.5},
            {"sku": "MCU-401", "name": "8-bit Microcontroller", "quantity": 1, "unit_cost": 8.25},
        ],
        "budget": 500.0,
    }
    response = client.post("/api/orders/restock", json=payload)
    assert response.status_code == 201
    assert response.json()["lead_time_days"] == 15
