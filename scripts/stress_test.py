"""Optional stress-test script for the risk propagation pipeline."""
import time
from statistics import mean

from data_ingestion.batch.simple_repository import SimpleRepository
from events.propagation.engine import PropagationEngine
from graph.loaders.builder import load_repository_into_graph
from graph.utils.graph_client import InMemoryGraphStore
from rag_pipeline.internet_search.null_adapter import NullInternetSearchAdapter
from rag_pipeline.llm_clients.fake_client import FakeLLMClient
from rag_pipeline.orchestration.pipeline import RAGPipeline
from rag_pipeline.reranking.null_reranker import NullReranker
from rag_pipeline.retrieval.memory_store import MemoryVectorStore
from synthetic_data.generators.events import generate_event
from synthetic_data.generators.network import generate_network
from synthetic_data.scenarios.definitions import SCENARIO_NAMES


def main():
    network = generate_network(
        num_regions=5,
        num_facilities=100,
        num_ports=10,
        num_suppliers=40,
        num_customers=80,
        num_materials=30,
        num_products=60,
        num_orders=500,
        num_shipments=600,
        num_routes=200,
        seed=42,
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

    graph_store = InMemoryGraphStore()
    load_repository_into_graph(repo, graph_store)

    engine = PropagationEngine(repo=repo, graph_store=graph_store, use_graph=True)
    pipeline = RAGPipeline(
        repo=repo,
        vector_store=MemoryVectorStore(),
        llm_client=FakeLLMClient(),
        propagation_engine=engine,
        reranker=NullReranker(),
        internet_search=NullInternetSearchAdapter(),
        max_chunks_per_call=5,
    )

    latencies = []
    errors = 0
    num_events = 100
    for i in range(num_events):
        scenario = SCENARIO_NAMES[i % len(SCENARIO_NAMES)]
        event, _ = generate_event(scenario, network, seed=i)
        repo.upsert(event)
        try:
            start = time.perf_counter()
            result = pipeline.analyze_event(event.id)
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)
            impacted = result["impact"]["impacted_entities"]
            print(f"event {i} ({scenario}): {len(impacted)} impacted, {elapsed:.3f}s")
        except Exception as exc:
            errors += 1
            print(f"event {i} ({scenario}): ERROR {exc}")

    if latencies:
        print("\nSummary")
        print(f"  events: {num_events}")
        print(f"  errors: {errors}")
        print(f"  avg latency: {mean(latencies):.3f}s")
        print(f"  max latency: {max(latencies):.3f}s")
    else:
        print("No successful events")


if __name__ == "__main__":
    main()
