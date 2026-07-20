"""Lightweight performance benchmarks for the RAG pipeline."""
import time

import pytest

from config.loader import Settings
from data_ingestion.batch.simple_repository import SimpleRepository
from events.propagation.engine import PropagationEngine
from graph.loaders.builder import load_repository_into_graph
from graph.utils.graph_client import InMemoryGraphStore
from models.events import PortClosure
from rag_pipeline.internet_search.null_adapter import NullInternetSearchAdapter
from rag_pipeline.llm_clients.fake_client import FakeLLMClient
from rag_pipeline.orchestration.pipeline import RAGPipeline
from rag_pipeline.reranking.null_reranker import NullReranker
from rag_pipeline.retrieval.memory_store import MemoryVectorStore
from synthetic_data.generators.events import generate_event
from synthetic_data.generators.network import generate_network


def _build_pipeline(use_graph: bool):
    network = generate_network(
        num_regions=2,
        num_facilities=20,
        num_ports=4,
        num_suppliers=10,
        num_customers=20,
        num_materials=10,
        num_products=15,
        num_orders=50,
        num_shipments=60,
        num_routes=25,
        seed=1,
    )
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

    graph_store = None
    if use_graph:
        graph_store = InMemoryGraphStore()
        load_repository_into_graph(repo, graph_store)

    engine = PropagationEngine(repo=repo, graph_store=graph_store, use_graph=use_graph)
    pipeline = RAGPipeline(
        repo=repo,
        vector_store=MemoryVectorStore(),
        llm_client=FakeLLMClient(),
        propagation_engine=engine,
        reranker=NullReranker(),
        internet_search=NullInternetSearchAdapter(),
        max_chunks_per_call=5,
    )
    return repo, pipeline, network


@pytest.mark.parametrize("use_graph", [False, True])
@pytest.mark.parametrize("scenario_name", ["port_closure", "cyber_incident", "export_control"])
def test_analyze_event_latency(use_graph: bool, scenario_name: str):
    repo, pipeline, network = _build_pipeline(use_graph=use_graph)
    event, _ = generate_event(scenario_name, network, seed=1)
    repo.upsert(event)

    start = time.perf_counter()
    result = pipeline.analyze_event(event.id)
    elapsed = time.perf_counter() - start

    assert result["event_id"] == event.id
    assert elapsed < 2.0, f"analyze_event took {elapsed:.2f}s, expected <2s"
