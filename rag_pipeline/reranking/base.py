"""Abstract reranker interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Reranker(ABC):
    """Rerank retrieved documents for relevance to a query."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int | None = None,
    ) -> List[Dict[str, Any]]:
        """Return the reranked subset of ``results``."""
