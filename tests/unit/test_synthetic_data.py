"""Tests for synthetic data generators and ground truth."""
import pytest

from synthetic_data.generators.events import generate_event
from synthetic_data.generators.network import generate_network
from synthetic_data.ground_truth.calculators import calculate_ground_truth
from synthetic_data.scenarios.definitions import SCENARIO_NAMES, run_scenario


def test_generate_network():
    network = generate_network(
        num_regions=2,
        num_facilities=10,
        num_ports=2,
        num_suppliers=5,
        num_customers=10,
        num_materials=5,
        num_products=8,
        num_orders=20,
        num_shipments=25,
        num_routes=15,
        seed=1,
    )
    assert len(network.regions) == 2
    assert len(network.orders) == 20
    assert len(network.shipments) == 25


@pytest.mark.parametrize("scenario_name", SCENARIO_NAMES)
def test_generate_event_for_each_scenario(scenario_name):
    network = generate_network(seed=1)
    event, ground_truth = generate_event(scenario_name, network, seed=1)
    assert event.id.startswith("EV_")
    assert "event_id" in ground_truth


@pytest.mark.parametrize("scenario_name", SCENARIO_NAMES)
def test_ground_truth_matches_event(scenario_name):
    network = generate_network(seed=2)
    event, _ = generate_event(scenario_name, network, seed=2)
    ground_truth = calculate_ground_truth(event, network)
    assert "event_id" in ground_truth
    assert len(ground_truth) >= 1


@pytest.mark.parametrize("scenario_name", SCENARIO_NAMES)
def test_run_scenario_minimal(scenario_name):
    result = run_scenario(
        scenario_name,
        use_graph=False,
        network_size={"num_regions": 2, "num_orders": 50, "num_shipments": 60, "num_routes": 20},
        seed=3,
    )
    assert result.scenario_name == scenario_name
    assert result.graph_enabled is False


@pytest.mark.parametrize("scenario_name", SCENARIO_NAMES)
def test_run_scenario_with_graph(scenario_name):
    result = run_scenario(
        scenario_name,
        use_graph=True,
        network_size={"num_regions": 2, "num_orders": 50, "num_shipments": 60, "num_routes": 20},
        seed=4,
    )
    assert result.scenario_name == scenario_name
    assert result.graph_enabled is True
