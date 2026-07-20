"""Integration tests for chunking and reranking in the RAG pipeline."""
from data_ingestion.batch.simple_repository import SimpleRepository
from events.propagation.engine import PropagationEngine
from models.domain import Customer, Facility, Order, Port, Product, Route, Shipment
from models.events import PortClosure
from rag_pipeline.chunking.simple_chunker import SimpleDocumentChunker
from rag_pipeline.internet_search.null_adapter import NullInternetSearchAdapter
from rag_pipeline.llm_clients.fake_client import FakeLLMClient
from rag_pipeline.orchestration.pipeline import RAGPipeline
from rag_pipeline.reranking.cross_encoder_reranker import CrossEncoderReranker
from rag_pipeline.retrieval.memory_store import MemoryVectorStore


def _build_pipeline_with_reranker():
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

    chunker = SimpleDocumentChunker(max_chunk_size=100)
    raw_docs = [
        {
            "id": "doc:port",
            "text": "Port closure playbook. Reroute shipments and notify customers.",
            "metadata": {"source_type": "playbook"},
        },
        {
            "id": "doc:cyber",
            "text": "Cyber incident playbook. Engage backup providers.",
            "metadata": {"source_type": "playbook"},
        },
    ]
    chunks = chunker.chunk(raw_docs)

    vector_store = MemoryVectorStore()
    vector_store.add_documents(chunks)

    def score_fn(query: str, text: str) -> float:
        return float(len(set(query.lower().split()) & set(text.lower().split())))

    engine = PropagationEngine(repo=repo)
    pipeline = RAGPipeline(
        repo=repo,
        vector_store=vector_store,
        llm_client=FakeLLMClient(),
        propagation_engine=engine,
        reranker=CrossEncoderReranker(score_fn=score_fn),
        internet_search=NullInternetSearchAdapter(),
        max_chunks_per_call=2,
    )
    return repo, pipeline


def test_pipeline_with_reranker_caps_chunks():
    repo, pipeline = _build_pipeline_with_reranker()
    event = PortClosure(id="EV1", port_id="P1")
    repo.upsert(event)
    result = pipeline.analyze_event("EV1")
    assert result["event_id"] == "EV1"
    assert result["retrieved_documents"] <= 2
