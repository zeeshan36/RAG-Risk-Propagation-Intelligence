"""Real internet search adapter (placeholder for external API integration)."""
from typing import Any, Dict, List

from common.exceptions import DependencyNotAvailableError
from rag_pipeline.internet_search.base import InternetSearchAdapter


try:
    import requests

    _HAS_REQUESTS = True
except Exception:  # pragma: no cover
    _HAS_REQUESTS = False


class RealInternetSearchAdapter(InternetSearchAdapter):
    """Calls an external search API.

    Requires a ``search_api_url`` and optionally an ``api_key``. This adapter is
    only active when ``USE_INTERNET_SEARCH=true``.
    """

    def __init__(
        self,
        search_api_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        if not _HAS_REQUESTS:
            raise DependencyNotAvailableError(
                "RealInternetSearchAdapter requires the 'requests' package."
            )
        self._search_api_url = search_api_url
        self._api_key = api_key
        self._calls = 0

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self._search_api_url:
            return []
        self._calls += 1
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        try:
            response = requests.get(
                self._search_api_url,
                params={"q": query, "limit": top_k},
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "text": item.get("snippet", ""),
                    "source_type": "internet_search",
                }
                for item in data.get("results", [])
            ]
        except Exception:
            return []

    def call_count(self) -> int:
        return self._calls
