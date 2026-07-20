"""Tests for vector store adapters."""
import pytest

from rag_pipeline.retrieval.base import VectorStore
from rag_pipeline.retrieval.chroma_store import ChromaVectorStore
from rag_pipeline.retrieval.memory_store import MemoryVectorStore


def test_memory_vector_store_search():
    store = MemoryVectorStore()
    store.add_documents(
        [
            {"id": "d1", "text": "port closure mitigation playbook", "metadata": {"cat": "playbook"}},
            {"id": "d2", "text": "cyber incident response plan", "metadata": {"cat": "playbook"}},
            {"id": "d3", "text": "quarterly financial report", "metadata": {"cat": "finance"}},
        ]
    )
    assert store.count() == 3
    results = store.search("port closure", top_k=2)
    assert len(results) == 2
    assert results[0]["id"] == "d1"

    filtered = store.search("playbook", filters={"cat": "playbook"}, top_k=5)
    assert len(filtered) >= 1


def test_memory_vector_store_clear():
    store = MemoryVectorStore()
    store.add_documents([{"id": "d1", "text": "text"}])
    store.clear()
    assert store.count() == 0


def test_chroma_store_requires_dependency():
    try:
        import chromadb  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError):
            ChromaVectorStore()
