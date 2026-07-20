"""End-to-end no-internet minimal-mode test."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from config.loader import load_settings
from synthetic_data.scenarios.definitions import run_scenario


@pytest.fixture
def no_internet_settings():
    config_dir = Path(__file__).parents[2] / "config"
    return load_settings(env="test_minimal_no_internet", config_dir=config_dir)


def test_settings_disable_all_external_features(no_internet_settings):
    features = no_internet_settings.features
    assert features.use_graph_db is False
    assert features.use_geospatial is False
    assert features.use_kafka_events is False
    assert features.use_internet_search is False
    assert features.use_reranker is False


def test_scenario_runs_without_internet(no_internet_settings):
    result = run_scenario(
        "port_closure",
        use_graph=False,
        network_size={"num_regions": 2, "num_orders": 50, "num_shipments": 60, "num_routes": 20},
        seed=7,
    )
    assert result.scenario_name == "port_closure"
    assert len(result.impact.impacted_entities) > 0


def test_api_runs_without_internet(no_internet_settings):
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

        response = client.post(
            "/scenarios/port_closure/run",
            json={
                "network_size": {
                    "num_regions": 2,
                    "num_orders": 30,
                    "num_shipments": 40,
                    "num_routes": 15,
                },
                "seed": 8,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["summary"]["impacted_entities"] > 0


def test_analysis_makes_no_internet_calls(no_internet_settings):
    with TestClient(app) as client:
        client.post("/entities/port", json={"id": "P_OFFLINE", "name": "Offline Port", "region_id": "R1"})
        client.post(
            "/events",
            json={"id": "EV_OFFLINE", "type": "PortClosure", "port_id": "P_OFFLINE", "severity": "low"},
        )
        response = client.get("/analysis/EV_OFFLINE")
        assert response.status_code == 200
        body = response.json()
        assert body["internet_search_calls"] == 0
