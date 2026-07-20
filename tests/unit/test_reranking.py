"""Tests for reranker adapters."""
import pytest

from rag_pipeline.reranking.cross_encoder_reranker import CrossEncoderReranker
from rag_pipeline.reranking.null_reranker import NullReranker


def test_null_reranker_passes_through():
    reranker = NullReranker()
    results = [
        {"id": "d1", "text": "alpha"},
        {"id": "d2", "text": "beta"},
    ]
    out = reranker.rerank("query", results, top_k=5)
    assert [r["id"] for r in out] == ["d1", "d2"]


def test_null_reranker_reduces_top_k():
    reranker = NullReranker()
    results = [{"id": f"d{i}"} for i in range(10)]
    out = reranker.rerank("query", results, top_k=3)
    assert len(out) == 3


def test_cross_encoder_reranker_changes_order():
    def score_fn(query: str, text: str) -> float:
        return float(len(set(query.lower().split()) & set(text.lower().split())))

    reranker = CrossEncoderReranker(score_fn=score_fn)
    results = [
        {"id": "d1", "text": "unrelated text here"},
        {"id": "d2", "text": "query match exact"},
    ]
    out = reranker.rerank("query match", results, top_k=1)
    assert len(out) == 1
    assert out[0]["id"] == "d2"


def test_cross_encoder_requires_dependency():
    from common.exceptions import DependencyNotAvailableError

    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        with pytest.raises(DependencyNotAvailableError):
            CrossEncoderReranker()
