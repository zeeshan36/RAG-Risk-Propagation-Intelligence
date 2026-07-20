"""Abstract document chunker interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class DocumentChunker(ABC):
    """Split raw documents into retrievable chunks with metadata."""

    @abstractmethod
    def chunk(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return a flat list of chunks.

        Each chunk must contain at least ``id``, ``text``, and ``metadata``.
        """
