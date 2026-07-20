"""Abstract vector store interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class VectorStore(ABC):
    """Adapter interface for vector-backed document retrieval."""

    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Index a list of documents with keys: id, text, metadata."""

    @abstractmethod
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Return the top-k matching documents."""

    @abstractmethod
    def count(self) -> int:
        """Return the number of indexed documents."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all indexed documents."""
