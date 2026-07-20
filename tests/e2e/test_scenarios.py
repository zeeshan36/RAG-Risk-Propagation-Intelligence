"""End-to-end scenario tests in minimal and mocked full modes."""
import pytest

from data_ingestion.batch.simple_repository import SimpleRepository
from events.propagation.engine import PropagationEngine
from graph.loaders.builder import load_repository_into_graph
from graph.utils.graph_client import InMemoryGraphStore
from synthetic_data.generators.events import generate_event
from synthetic_data.generators.network import generate_network
from synthetic_data.ground_truth.calculators import calculate_ground_truth
from synthetic_data.scenarios.definitions import SCENARIO_NAMES, run_scenario


def _ground_truth_overlap(impact, ground_truth) -> bool:
    """Return True if at least one impacted ID set overlaps the ground truth."""
    for key, expected_ids in ground_truth.items():
        if not expected_ids:
            continue
        impacted_attr = {
            "impacted_route_ids": impact.impacted_route_ids,
            "impacted_shipment_ids": impact.impacted_shipment_ids,
            "impacted_order_ids": impact.impacted_order_ids,
            "impacted_product_ids": impact.impacted_product_ids,
            "impacted_facility_ids": impact.impacted_facility_ids,
        }.get(key, [])
        if set(impacted_attr) & set(expected_ids):
            return True
    return False


@pytest.mark.parametrize("scenario_name", SCENARIO_NAMES)
def test_scenario_minimal_matches_ground_truth(scenario_name):
    result = run_scenario(
        scenario_name,
        use_graph=False,
        network_size={"num_regions": 3, "num_orders": 100, "num_shipments": 120, "num_routes": 40},
        seed=42,
    )
    assert result.scenario_name == scenario_name
    assert result.graph_enabled is False
    assert _ground_truth_overlap(result.impact, result.ground_truth) is True


@pytest.mark.parametrize("scenario_name", SCENARIO_NAMES)
def test_scenario_graph_matches_ground_truth(scenario_name):
    result = run_scenario(
        scenario_name,
        use_graph=True,
        network_size={"num_regions": 3, "num_orders": 100, "num_shipments": 120, "num_routes": 40},
        seed=42,
    )
    assert result.scenario_name == scenario_name
    assert result.graph_enabled is True
    assert _ground_truth_overlap(result.impact, result.ground_truth) is True


@pytest.mark.parametrize("scenario_name", SCENARIO_NAMES)
def test_graph_and_rule_engine_produce_similar_results(scenario_name):
    network = generate_network(
        num_regions=3,
        num_orders=100,
        num_shipments=120,
        num_routes=40,
        seed=42,
    )
    event, _ = generate_event(scenario_name, network, seed=42)
    repo = SimpleRepository()
    for entity_list in (
        network.regions,
        network.facilities,
        network.ports,
        network.suppliers,
        network.customers,
        network.materials,
        network.products,
        network.routes,
        network.orders,
        network.shipments,
        network.contracts,
        network.revenue_streams,
    ):
        repo.load_many(entity_list)
    repo.upsert(event)

    rule_engine = PropagationEngine(repo=repo, use_graph=False)
    rule_impact = rule_engine.propagate(event)

    graph = InMemoryGraphStore()
    load_repository_into_graph(repo, graph)
    graph_engine = PropagationEngine(repo=repo, graph_store=graph, use_graph=True)
    graph_impact = graph_engine.propagate(event)

    # Both engines should find at least one overlapping impacted shipment/order.
    assert (
        set(rule_impact.impacted_order_ids) & set(graph_impact.impacted_order_ids)
        or set(rule_impact.impacted_shipment_ids) & set(graph_impact.impacted_shipment_ids)
    )
