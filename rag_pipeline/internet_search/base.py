"""Abstract internet search adapter for augmenting RAG context."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class InternetSearchAdapter(ABC):
    """Search the public internet for additional risk context."""

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Return a list of search result snippets.

        Each result should contain at least ``title``, ``url``, and ``text``.
        """

    @abstractmethod
    def call_count(self) -> int:
        """Return the number of external search calls made."""
