"""No-op reranker used when reranking is disabled."""
from typing import Any, Dict, List

from rag_pipeline.reranking.base import Reranker


class NullReranker(Reranker):
    """Returns results unchanged."""

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int | None = None,
    ) -> List[Dict[str, Any]]:
        if top_k is not None:
            return results[:top_k]
        return results
