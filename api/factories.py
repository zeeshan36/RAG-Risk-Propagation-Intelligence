"""Factory functions for assembling adapters based on configuration."""
import os
from typing import List, Optional

from config.loader import Settings
from data_ingestion.batch.simple_repository import SimpleRepository
from data_ingestion.mappers.geospatial import GeoMapper, NoOpGeoMapper, ShapelyGeoMapper
from events.propagation.engine import PropagationEngine
from graph.loaders.builder import load_repository_into_graph
from graph.utils.graph_client import GraphStore, InMemoryGraphStore, Neo4jGraphStore
from rag_pipeline.chunking.base import DocumentChunker
from rag_pipeline.chunking.simple_chunker import SimpleDocumentChunker
from rag_pipeline.internet_search.base import InternetSearchAdapter
from rag_pipeline.internet_search.null_adapter import NullInternetSearchAdapter
from rag_pipeline.internet_search.real_adapter import RealInternetSearchAdapter
from rag_pipeline.llm_clients.base import LLMClient
from rag_pipeline.llm_clients.fake_client import FakeLLMClient
from rag_pipeline.llm_clients.openai_client import OpenAILLMClient
from rag_pipeline.llm_clients.openai_compatible_client import (
    OpenAICompatibleLLMClient,
)
from rag_pipeline.orchestration.pipeline import RAGPipeline
from rag_pipeline.reranking.base import Reranker
from rag_pipeline.reranking.cross_encoder_reranker import CrossEncoderReranker
from rag_pipeline.reranking.null_reranker import NullReranker
from rag_pipeline.retrieval.base import VectorStore
from rag_pipeline.retrieval.chroma_store import ChromaVectorStore
from rag_pipeline.retrieval.memory_store import MemoryVectorStore


def build_vector_store(settings: Settings) -> VectorStore:
    provider = settings.vector_store.provider
    if provider == "chroma":
        return ChromaVectorStore(
            collection_name=settings.vector_store.collection_name,
            persist_directory=settings.vector_store.persist_directory,
        )
    return MemoryVectorStore()


_PROVIDER_ENV_KEYS = {
    "openai": ["OPENAI_API_KEY"],
    "copilot": ["COPILOT_API_KEY", "GITHUB_TOKEN"],
    "kimi": ["MOONSHOT_API_KEY"],
    "openrouter": ["OPENROUTER_API_KEY"],
}

_PROVIDER_DEFAULT_BASE_URL = {
    "openai": None,
    "copilot": "https://api.githubcopilot.com/chat/completions",
    "kimi": "https://api.moonshot.cn/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}


def _api_key_for_provider(provider: str, settings: Settings) -> Optional[str]:
    """Return the configured API key or the first matching env-var fallback."""
    if settings.llm.api_key:
        return settings.llm.api_key
    for env_var in _PROVIDER_ENV_KEYS.get(provider, []):
        value = os.getenv(env_var)
        if value:
            return value
    return None


def build_llm_client(settings: Settings) -> LLMClient:
    provider = settings.llm.provider
    if provider == "fake":
        return FakeLLMClient()

    base_url = settings.llm.base_url or _PROVIDER_DEFAULT_BASE_URL[provider]
    api_key = _api_key_for_provider(provider, settings)
    common_kwargs = {
        "model": settings.llm.model,
        "temperature": settings.llm.temperature,
        "max_tokens": settings.llm.max_tokens,
        "api_key": api_key,
        "base_url": base_url,
    }

    if provider == "openai":
        return OpenAILLMClient(**common_kwargs)
    return OpenAICompatibleLLMClient(provider=provider, **common_kwargs)


def build_geo_mapper(settings: Settings) -> GeoMapper:
    if settings.features.use_geospatial:
        return ShapelyGeoMapper()
    return NoOpGeoMapper()


def build_graph_store(settings: Settings) -> Optional[GraphStore]:
    if not settings.features.use_graph_db:
        return None
    if settings.graph_db.provider == "neo4j":
        return Neo4jGraphStore(
            uri=settings.graph_db.uri,
            user=settings.graph_db.user,
            password=settings.graph_db.password,
        )
    return InMemoryGraphStore()


def build_chunker(settings: Settings) -> DocumentChunker:
    if not settings.chunking.use_chunker:
        # Return a pass-through chunker that still normalizes documents.
        return SimpleDocumentChunker(
            max_chunk_size=settings.chunking.max_chunk_size,
            preserve_tables=False,
        )
    return SimpleDocumentChunker(
        max_chunk_size=settings.chunking.max_chunk_size,
        preserve_tables=settings.chunking.preserve_tables,
        heading_regex=settings.chunking.heading_regex,
    )


def build_reranker(settings: Settings) -> Reranker:
    if not settings.reranker.use_reranker:
        return NullReranker()
    return CrossEncoderReranker(model_name=settings.reranker.model)


def build_internet_search(settings: Settings) -> InternetSearchAdapter:
    if not settings.features.use_internet_search:
        return NullInternetSearchAdapter()
    return RealInternetSearchAdapter(
        search_api_url=settings.internet_search.search_api_url,
        api_key=settings.internet_search.api_key,
    )


def build_propagation_engine(
    settings: Settings,
    repo: SimpleRepository,
    graph_store: Optional[GraphStore],
    geo_mapper: GeoMapper,
) -> PropagationEngine:
    return PropagationEngine(
        repo=repo,
        graph_store=graph_store,
        geo_mapper=geo_mapper,
        use_graph=settings.features.use_graph_db,
    )


def build_pipeline(
    repo: SimpleRepository,
    vector_store: VectorStore,
    llm_client: LLMClient,
    propagation_engine: PropagationEngine,
    reranker: Reranker,
    internet_search: InternetSearchAdapter,
    settings: Settings,
) -> RAGPipeline:
    return RAGPipeline(
        repo=repo,
        vector_store=vector_store,
        llm_client=llm_client,
        propagation_engine=propagation_engine,
        reranker=reranker,
        internet_search=internet_search,
        max_chunks_per_call=settings.max_chunks_per_call,
    )


def chunk_documents(chunker: DocumentChunker, documents: List[dict]) -> List[dict]:
    """Normalize and chunk a list of documents."""
    normalized = []
    for doc in documents:
        meta = dict(doc.get("metadata", {}) or {})
        meta.setdefault("source_type", "document")
        normalized.append(
            {
                "id": doc.get("id", ""),
                "text": doc.get("text", ""),
                "metadata": meta,
            }
        )
    return chunker.chunk(normalized)


def seed_vector_store(
    repo: SimpleRepository,
    vector_store: VectorStore,
    chunker: DocumentChunker,
) -> None:
    """Index a small set of playbook/contract snippets for retrieval."""
    from models.domain import Contract

    docs = [
        {
            "id": "doc:port_closure_playbook",
            "text": (
                "Port closure playbook\n\n"
                "Identify impacted routes, find alternative ports, notify customers, "
                "activate force majeure clauses if applicable."
            ),
            "metadata": {"source_type": "playbook", "entity_ids": []},
        },
        {
            "id": "doc:cyber_incident_playbook",
            "text": (
                "Cyber incident playbook\n\n"
                "Switch to manual tracking, engage backup logistics providers, "
                "inform customers of expected delays."
            ),
            "metadata": {"source_type": "playbook", "entity_ids": []},
        },
        {
            "id": "doc:weather_playbook",
            "text": (
                "Extreme weather playbook\n\n"
                "Reposition inventory, reroute shipments, prioritize high-margin orders."
            ),
            "metadata": {"source_type": "playbook", "entity_ids": []},
        },
    ]
    for contract in repo.list(Contract):
        docs.append(
            {
                "id": f"doc:contract:{contract.id}",
                "text": (
                    f"Contract {contract.id}\n\n"
                    f"SLA {contract.sla_days} days, "
                    f"penalty {contract.penalty_per_day} per day, "
                    f"force majeure {'yes' if contract.force_majeure_clause else 'no'}."
                ),
                "metadata": {
                    "source_type": "contract",
                    "entity_ids": [contract.customer_id] if contract.customer_id else [],
                    "customer_id": contract.customer_id,
                },
            }
        )
    if docs:
        chunks = chunk_documents(chunker, docs)
        vector_store.add_documents(chunks)
