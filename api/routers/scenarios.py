"""Scenario execution endpoints."""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from api.dependencies import (
    LoggerDep,
    PipelineDep,
    PropagationEngineDep,
    RepoDep,
    SettingsDep,
)
from api.schemas import ScenarioRunResponse
from synthetic_data.generators.events import generate_event
from synthetic_data.generators.network import generate_network
from synthetic_data.ground_truth.calculators import calculate_ground_truth
from synthetic_data.scenarios.definitions import SCENARIO_NAMES

router = APIRouter(tags=["scenarios"])


@router.post("/scenarios/{scenario_name}/run", response_model=ScenarioRunResponse)
def run_scenario(
    scenario_name: str,
    payload: Dict[str, Any],
    settings: SettingsDep,
    repo: RepoDep,
    engine: PropagationEngineDep,
    pipeline: PipelineDep,
    logger: LoggerDep,
):
    """Run a named synthetic scenario end-to-end."""
    if scenario_name not in SCENARIO_NAMES:
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {scenario_name}")

    logger.info("Running scenario", extra={"scenario": scenario_name})
    network_size = payload.get("network_size", {}) or {}
    seed = payload.get("seed", 42)

    network = generate_network(**network_size, seed=seed)
    event, generator_ground_truth = generate_event(scenario_name, network, seed=seed)
    ground_truth = calculate_ground_truth(event, network)

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

    # Refresh graph if enabled so the scenario data is traversable.
    if settings.features.use_graph_db and settings.graph_db.provider == "memory":
        from graph.loaders.builder import load_repository_into_graph
        from graph.utils.graph_client import InMemoryGraphStore

        graph_store = InMemoryGraphStore()
        load_repository_into_graph(repo, graph_store)
        engine.graph_store = graph_store

    impact = engine.propagate(event)
    analysis = pipeline.analyze_event(event.id)

    summary: Dict[str, Any] = {
        "scenario": scenario_name,
        "graph_enabled": settings.features.use_graph_db,
        "geo_enabled": settings.features.use_geospatial,
        "entities_in_repo": repo.type_count(),
        "impacted_entities": len(impact.impacted_entities),
        "estimated_revenue_at_risk": impact.estimated_revenue_at_risk,
        "ground_truth_keys": list(ground_truth.keys()),
        "analysis": {
            "retrieved_documents": analysis.get("retrieved_documents", 0),
            "llm_metadata": analysis.get("llm_metadata", {}),
        },
    }
    return ScenarioRunResponse(scenario_name=scenario_name, summary=summary)
