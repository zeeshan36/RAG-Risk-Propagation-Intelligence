"""No-op internet search adapter used in minimal/offline mode."""
from typing import Any, Dict, List

from rag_pipeline.internet_search.base import InternetSearchAdapter


class NullInternetSearchAdapter(InternetSearchAdapter):
    """Returns empty results and never makes external calls."""

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return []

    def call_count(self) -> int:
        return 0
