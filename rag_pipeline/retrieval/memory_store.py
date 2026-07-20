"""In-memory vector store for tests and minimal-mode fallback."""
from typing import Any, Dict, List, Optional

from rag_pipeline.retrieval.base import VectorStore


class MemoryVectorStore(VectorStore):
    """Keyword-ish in-memory vector store.

    Scores documents by the number of query tokens present in the document
    text, with optional metadata equality filters.
    """

    def __init__(self) -> None:
        self._docs: Dict[str, Dict[str, Any]] = {}

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        for doc in documents:
            doc_id = doc.get("id")
            if not doc_id:
                raise ValueError("Document must have an 'id' field")
            self._docs[doc_id] = doc

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        filters = filters or {}
        query_tokens = {t.lower() for t in query.split() if t}
        scored: List[tuple] = []
        for doc in self._docs.values():
            meta = doc.get("metadata", {}) or {}
            if any(meta.get(k) != v for k, v in filters.items()):
                continue
            text = str(doc.get("text", "")).lower()
            score = sum(1 for token in query_tokens if token in text)
            if score > 0 or not query_tokens:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    def count(self) -> int:
        return len(self._docs)

    def clear(self) -> None:
        self._docs.clear()
