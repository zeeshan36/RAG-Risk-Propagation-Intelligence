"""Tests for the RAG orchestration pipeline."""
import pytest

from data_ingestion.batch.simple_repository import SimpleRepository
from events.propagation.engine import PropagationEngine
from models.domain import Customer, Facility, Order, Port, Product, Route, Shipment
from models.events import PortClosure
from rag_pipeline.internet_search.null_adapter import NullInternetSearchAdapter
from rag_pipeline.llm_clients.fake_client import FakeLLMClient
from rag_pipeline.orchestration.pipeline import RAGPipeline
from rag_pipeline.reranking.null_reranker import NullReranker
from rag_pipeline.retrieval.memory_store import MemoryVectorStore


def _setup():
    repo = SimpleRepository()
    repo.load_many([
        Port(id="P1", name="Port A", region_id="R1"),
        Facility(id="F1", type="warehouse", name="WH1", region_id="R1"),
        Customer(id="C1", name="Customer A", region_id="R1", criticality_score=0.5),
        Product(id="PR1", name="Product A", sku="SKU1"),
        Route(id="R1", origin_node_id="P1", destination_node_id="F1", mode="sea", avg_lead_time_days=5, capacity=100),
        Order(id="O1", customer_id="C1", product_id="PR1", quantity=10),
        Shipment(id="SH1", order_id="O1", route_ids=["R1"], carrier_id="CAR1"),
    ])
    vector_store = MemoryVectorStore()
    vector_store.add_documents([
        {"id": "doc1", "text": "Port closure playbook: reroute shipments.", "metadata": {"category": "playbook"}},
    ])
    llm = FakeLLMClient()
    engine = PropagationEngine(repo=repo)
    pipeline = RAGPipeline(
        repo,
        vector_store,
        llm,
        engine,
        reranker=NullReranker(),
        internet_search=NullInternetSearchAdapter(),
    )
    return repo, pipeline


def test_analyze_event():
    repo, pipeline = _setup()
    event = PortClosure(id="EV1", port_id="P1")
    repo.upsert(event)
    result = pipeline.analyze_event("EV1")
    assert result["event_id"] == "EV1"
    assert result["event_type"] == "PortClosure"
    assert result["retrieved_documents"] >= 0
    assert "impact_narrative" in result
    assert "mitigation_narrative" in result


def test_analyze_missing_event():
    _, pipeline = _setup()
    with pytest.raises(ValueError):
        pipeline.analyze_event("MISSING")
