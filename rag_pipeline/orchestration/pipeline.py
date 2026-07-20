"""RAG orchestration pipeline for event impact analysis."""
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from events.propagation.engine import PropagationEngine
from rag_pipeline.internet_search.base import InternetSearchAdapter
from rag_pipeline.llm_clients.base import LLMClient
from rag_pipeline.prompts.loader import render_impact_analysis, render_mitigation_plan
from rag_pipeline.reranking.base import Reranker
from rag_pipeline.retrieval.base import VectorStore

if TYPE_CHECKING:
    from data_ingestion.batch.simple_repository import SimpleRepository
    from models.events import Event

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Orchestrates propagation, retrieval, reranking, and LLM generation."""

    def __init__(
        self,
        repo: "SimpleRepository",
        vector_store: VectorStore,
        llm_client: LLMClient,
        propagation_engine: PropagationEngine,
        reranker: Reranker,
        internet_search: InternetSearchAdapter,
        max_chunks_per_call: int = 10,
    ) -> None:
        self.repo = repo
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.propagation_engine = propagation_engine
        self.reranker = reranker
        self.internet_search = internet_search
        self.max_chunks_per_call = max_chunks_per_call

    def analyze_event(self, event_id: str) -> Dict[str, Any]:
        """Run full impact analysis for an event."""
        event = self._find_event(event_id)
        if event is None:
            raise ValueError(f"Event {event_id} not found")

        impact = self.propagation_engine.propagate(event)
        context_docs = self._retrieve_context(event)
        context_docs = self._rerank_and_cap(event, context_docs)

        impact_prompt = render_impact_analysis(
            {
                "event": event.model_dump(),
                "impacted_entities": [e.model_dump() for e in impact.impacted_entities],
                "context_docs": [{"text": d.get("text", "")} for d in context_docs],
            }
        )
        impact_narrative = self.llm_client.generate(impact_prompt)

        mitigation_prompt = render_mitigation_plan(
            {
                "event": event.model_dump(),
                "impacted_entities": [e.model_dump() for e in impact.impacted_entities],
            }
        )
        mitigation_narrative = self.llm_client.generate(mitigation_prompt)

        return {
            "event_id": event_id,
            "event_type": event.type,
            "impact": impact.model_dump(),
            "retrieved_documents": len(context_docs),
            "internet_search_calls": self.internet_search.call_count(),
            "impact_narrative": impact_narrative,
            "mitigation_narrative": mitigation_narrative,
            "llm_metadata": self.llm_client.generation_metadata(),
        }

    def _find_event(self, event_id: str) -> Optional["Event"]:
        from models.events import (
            CyberIncident,
            ExportControl,
            ExtremeWeather,
            PoliticalUnrest,
            PortClosure,
        )

        for event_cls in (
            PortClosure,
            ExtremeWeather,
            CyberIncident,
            ExportControl,
            PoliticalUnrest,
        ):
            try:
                return self.repo.get(event_cls, event_id)
            except Exception:
                continue
        return None

    def _retrieve_context(self, event: "Event") -> List[Dict[str, Any]]:
        query = f"{event.type} supply chain disruption mitigation"
        vector_results = self.vector_store.search(query, top_k=10)

        if self.internet_search.call_count() == 0:
            # Only call internet search if it is enabled; the null adapter
            # returns an empty list without making network requests.
            internet_results = self.internet_search.search(query, top_k=3)
            for r in internet_results:
                r.setdefault("metadata", {})["source_type"] = "internet_search"
            vector_results = vector_results + internet_results

        return vector_results

    def _rerank_and_cap(
        self, event: "Event", docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        before = len(docs)
        reranked = self.reranker.rerank(
            f"{event.type} supply chain disruption",
            docs,
            top_k=self.max_chunks_per_call,
        )
        after = len(reranked)
        logger.info(
            "Reranked context documents",
            extra={
                "before_rerank": before,
                "after_rerank": after,
                "max_chunks_per_call": self.max_chunks_per_call,
            },
        )
        return reranked[: self.max_chunks_per_call]
