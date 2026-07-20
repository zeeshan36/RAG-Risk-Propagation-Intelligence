"""Fail-safe behavior when optional dependencies are missing."""
import sys
from pathlib import Path

import pytest

from config.loader import Settings


def _block_import(monkeypatch, module_name: str):
    """Block a module import by setting it to None in sys.modules."""
    monkeypatch.setitem(sys.modules, module_name, None)


def test_minimal_adapters_work_without_optional_dependencies():
    from api.factories import (
        build_chunker,
        build_geo_mapper,
        build_graph_store,
        build_internet_search,
        build_llm_client,
        build_reranker,
        build_vector_store,
    )

    settings = Settings()
    assert build_vector_store(settings) is not None
    assert build_llm_client(settings) is not None
    assert build_geo_mapper(settings) is not None
    assert build_graph_store(settings) is None
    assert build_chunker(settings) is not None
    assert build_reranker(settings) is not None
    assert build_internet_search(settings) is not None


def test_chroma_store_fails_gracefully_when_missing(monkeypatch):
    _block_import(monkeypatch, "chromadb")
    from rag_pipeline.retrieval.chroma_store import ChromaVectorStore

    with pytest.raises(ImportError):
        ChromaVectorStore()


def test_openai_client_fails_gracefully_when_missing(monkeypatch):
    _block_import(monkeypatch, "openai")
    from rag_pipeline.llm_clients.openai_client import OpenAILLMClient

    with pytest.raises(ImportError):
        OpenAILLMClient(api_key="test")


def test_neo4j_graph_store_fails_gracefully_when_missing(monkeypatch):
    _block_import(monkeypatch, "neo4j")
    from graph.utils.graph_client import Neo4jGraphStore

    with pytest.raises(ImportError):
        Neo4jGraphStore("bolt://localhost:7687", "neo4j", "password")


def test_shapely_mapper_fails_gracefully_when_missing(monkeypatch):
    _block_import(monkeypatch, "shapely")
    from data_ingestion.mappers.geospatial import ShapelyGeoMapper

    with pytest.raises(ImportError):
        ShapelyGeoMapper()


def test_kafka_consumer_fails_gracefully_when_missing(monkeypatch):
    _block_import(monkeypatch, "kafka")
    from data_ingestion.streaming.consumer import KafkaEventConsumer

    with pytest.raises(ImportError):
        KafkaEventConsumer(bootstrap_servers=["localhost:9092"], topic="t", group_id="g")


def test_cross_encoder_reranker_fails_gracefully_when_missing(monkeypatch):
    _block_import(monkeypatch, "sentence_transformers")
    from common.exceptions import DependencyNotAvailableError
    from rag_pipeline.reranking.cross_encoder_reranker import CrossEncoderReranker

    with pytest.raises(DependencyNotAvailableError):
        CrossEncoderReranker()


def test_real_internet_search_fails_gracefully_when_requests_missing(monkeypatch):
    _block_import(monkeypatch, "requests")
    from common.exceptions import DependencyNotAvailableError
    from rag_pipeline.internet_search.real_adapter import RealInternetSearchAdapter

    with pytest.raises(DependencyNotAvailableError):
        RealInternetSearchAdapter()
