"""End-to-end synthetic scenario definitions."""
from dataclasses import dataclass
from typing import Any, Callable, Dict

from events.propagation.engine import PropagationEngine
from events.propagation.impact_result import ImpactResult
from graph.loaders.builder import load_repository_into_graph
from graph.utils.graph_client import InMemoryGraphStore
from models.events import Event
from synthetic_data.generators.events import generate_event
from synthetic_data.generators.network import SupplyChainNetwork, generate_network
from synthetic_data.ground_truth.calculators import calculate_ground_truth


@dataclass
class ScenarioResult:
    scenario_name: str
    event: Event
    impact: ImpactResult
    ground_truth: Dict[str, Any]
    graph_enabled: bool


SCENARIO_NAMES = [
    "port_closure",
    "extreme_weather",
    "cyber_incident",
    "export_control",
    "political_unrest",
]


def run_scenario(
    scenario_name: str,
    use_graph: bool = False,
    network_size: Dict[str, Any] | None = None,
    seed: int = 42,
) -> ScenarioResult:
    """Generate a synthetic network, fire an event, and run propagation."""
    if scenario_name not in SCENARIO_NAMES:
        raise ValueError(f"Unknown scenario: {scenario_name}")

    network_size = network_size or {}
    network = generate_network(**network_size, seed=seed)
    event, ground_truth = generate_event(scenario_name, network, seed=seed)

    from data_ingestion.batch.simple_repository import SimpleRepository

    repo = SimpleRepository()
    repo.load_many(network.regions)
    repo.load_many(network.facilities)
    repo.load_many(network.ports)
    repo.load_many(network.suppliers)
    repo.load_many(network.customers)
    repo.load_many(network.materials)
    repo.load_many(network.products)
    repo.load_many(network.routes)
    repo.load_many(network.orders)
    repo.load_many(network.shipments)
    repo.load_many(network.contracts)
    repo.load_many(network.revenue_streams)

    graph_store = None
    if use_graph:
        graph_store = InMemoryGraphStore()
        load_repository_into_graph(repo, graph_store)

    engine = PropagationEngine(repo=repo, graph_store=graph_store, use_graph=use_graph)
    impact = engine.propagate(event)
    return ScenarioResult(
        scenario_name=scenario_name,
        event=event,
        impact=impact,
        ground_truth=calculate_ground_truth(event, network),
        graph_enabled=use_graph,
    )


def list_scenarios() -> list[str]:
    return list(SCENARIO_NAMES)
