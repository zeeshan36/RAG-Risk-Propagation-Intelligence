"""Cross-encoder reranker adapter."""
from typing import Any, Callable, Dict, List, Optional

from common.exceptions import DependencyNotAvailableError
from rag_pipeline.reranking.base import Reranker

try:
    from sentence_transformers import CrossEncoder

    _HAS_SENTENCE_TRANSFORMERS = True
except Exception:  # pragma: no cover
    _HAS_SENTENCE_TRANSFORMERS = False


class CrossEncoderReranker(Reranker):
    """Reranks results with a cross-encoder model.

    Requires the optional ``sentence-transformers`` dependency. For tests a
    custom ``score_fn`` can be injected.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        score_fn: Optional[Callable[[str, str], float]] = None,
    ) -> None:
        self._model_name = model_name
        self._score_fn = score_fn
        self._model: Any = None
        if score_fn is None:
            if not _HAS_SENTENCE_TRANSFORMERS:
                raise DependencyNotAvailableError(
                    "CrossEncoderReranker requires sentence-transformers to be installed "
                    "(pip install sentence-transformers)."
                )
            self._model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int | None = None,
    ) -> List[Dict[str, Any]]:
        if not results:
            return []

        scored = []
        for result in results:
            text = result.get("text", "")
            if self._score_fn:
                score = self._score_fn(query, text)
            else:
                score = float(self._model.predict([[query, text]])[0])
            scored.append((score, result))

        scored.sort(key=lambda x: x[0], reverse=True)
        reranked = [result for _, result in scored]
        if top_k is not None:
            return reranked[:top_k]
        return reranked
