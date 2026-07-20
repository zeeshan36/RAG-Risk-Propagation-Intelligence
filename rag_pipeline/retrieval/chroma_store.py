"""ChromaDB vector store adapter."""
from typing import Any, Dict, List, Optional

from rag_pipeline.retrieval.base import VectorStore

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    _HAS_CHROMA = True
except Exception:  # pragma: no cover
    _HAS_CHROMA = False


class ChromaVectorStore(VectorStore):
    """In-process Chroma vector store.

    Requires the optional `chromadb` dependency.
    """

    def __init__(
        self,
        collection_name: str = "supply_chain_docs",
        persist_directory: Optional[str] = None,
        embedding_function: Optional[Any] = None,
    ) -> None:
        if not _HAS_CHROMA:
            raise ImportError(
                "ChromaVectorStore requires chromadb to be installed "
                "(pip install rag-risk-propagation[vector])."
            )
        settings = ChromaSettings(
            persist_directory=persist_directory or "./data/chroma",
            anonymized_telemetry=False,
        )
        self._client = chromadb.Client(settings)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc.get("metadata", {}) or {} for doc in documents]
        self._collection.add(ids=ids, documents=texts, metadatas=metadatas)

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        results = self._collection.query(
            query_texts=[query],
            n_results=top_k,
            where=filters or None,
        )
        documents: List[Dict[str, Any]] = []
        ids = results.get("ids", [[]])[0]
        texts = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        for i, doc_id in enumerate(ids):
            documents.append(
                {
                    "id": doc_id,
                    "text": texts[i] if texts else "",
                    "metadata": metadatas[i] if metadatas else {},
                    "score": distances[i] if distances else None,
                }
            )
        return documents

    def count(self) -> int:
        return self._collection.count()

    def clear(self) -> None:
        self._client.delete_collection(self._collection.name)
        self._collection = self._client.get_or_create_collection(
            name=self._collection.name
        )
