"""Integration tests for the FastAPI application."""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness(client: TestClient):
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert "vector_documents" in body


def test_metrics(client: TestClient):
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "features" in body


def test_ingest_and_get_entity(client: TestClient):
    payload = {
        "id": "P1",
        "name": "Port A",
        "region_id": "R1",
        "modes": ["sea"],
    }
    response = client.post("/entities/port", json=payload)
    assert response.status_code == 200

    response = client.get("/entities/port")
    assert response.status_code == 200
    assert any(e["id"] == "P1" for e in response.json())


def test_ingest_and_get_event(client: TestClient):
    payload = {
        "id": "EV_PORT_1",
        "type": "PortClosure",
        "port_id": "P1",
        "severity": "high",
        "expected_duration_hours": 48,
    }
    response = client.post("/events", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == "EV_PORT_1"
    assert body["event_type"] == "PortClosure"

    response = client.get("/events/EV_PORT_1")
    assert response.status_code == 200
    assert response.json()["port_id"] == "P1"


def test_impact_endpoint(client: TestClient):
    # Seed a minimal network and event.
    client.post("/entities/port", json={"id": "P2", "name": "Port B", "region_id": "R1"})
    client.post(
        "/entities/route",
        json={
            "id": "R1",
            "origin_node_id": "P2",
            "destination_node_id": "F1",
            "mode": "sea",
            "avg_lead_time_days": 5,
            "capacity": 100,
        },
    )
    client.post(
        "/entities/shipment",
        json={"id": "SH1", "order_id": "O1", "route_ids": ["R1"], "carrier_id": "CAR1"},
    )
    client.post("/entities/order", json={"id": "O1", "customer_id": "C1", "product_id": "PR1", "quantity": 10})
    client.post("/entities/customer", json={"id": "C1", "name": "Customer", "region_id": "R1", "criticality_score": 0.5})
    client.post("/entities/product", json={"id": "PR1", "name": "Product", "sku": "SKU1"})

    client.post(
        "/events",
        json={"id": "EV2", "type": "PortClosure", "port_id": "P2", "severity": "medium"},
    )
    response = client.get("/impact/EV2")
    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == "EV2"
    assert any(e["entity_type"] == "Shipment" and e["entity_id"] == "SH1" for e in body["impacted_entities"])


def test_analysis_endpoint(client: TestClient):
    client.post("/entities/port", json={"id": "P3", "name": "Port C", "region_id": "R1"})
    client.post(
        "/events",
        json={"id": "EV3", "type": "PortClosure", "port_id": "P3", "severity": "low"},
    )
    response = client.get("/analysis/EV3")
    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == "EV3"
    assert "impact_narrative" in body


def test_impact_not_found(client: TestClient):
    response = client.get("/impact/missing")
    assert response.status_code == 404


def test_run_scenario(client: TestClient):
    response = client.post(
        "/scenarios/port_closure/run",
        json={"network_size": {"num_regions": 2, "num_orders": 50, "num_shipments": 60, "num_routes": 20}, "seed": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["scenario_name"] == "port_closure"
    assert body["status"] == "completed"
    assert body["summary"]["impacted_entities"] >= 0
