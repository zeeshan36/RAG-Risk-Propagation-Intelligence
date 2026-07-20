"""FastAPI dependency providers."""
from typing import Annotated, Optional

from fastapi import Depends, Request

from common.logging import get_logger
from config.loader import Settings
from data_ingestion.batch.simple_repository import SimpleRepository
from events.propagation.engine import PropagationEngine
from graph.utils.graph_client import GraphStore
from rag_pipeline.chunking.base import DocumentChunker
from rag_pipeline.internet_search.base import InternetSearchAdapter
from rag_pipeline.llm_clients.base import LLMClient
from rag_pipeline.orchestration.pipeline import RAGPipeline
from rag_pipeline.reranking.base import Reranker
from rag_pipeline.retrieval.base import VectorStore


def get_settings(request: Request) -> Settings:
    """Return app settings from application state."""
    return request.app.state.settings


def get_repo(request: Request) -> SimpleRepository:
    """Return the in-memory repository from application state."""
    return request.app.state.repo


def get_vector_store(request: Request) -> VectorStore:
    """Return the vector store from application state."""
    return request.app.state.vector_store


def get_llm_client(request: Request) -> LLMClient:
    """Return the LLM client from application state."""
    return request.app.state.llm_client


def get_graph_store(request: Request) -> Optional[GraphStore]:
    """Return the graph store from application state if configured."""
    return getattr(request.app.state, "graph_store", None)


def get_chunker(request: Request) -> DocumentChunker:
    """Return the document chunker from application state."""
    return request.app.state.chunker


def get_reranker(request: Request) -> Reranker:
    """Return the reranker from application state."""
    return request.app.state.reranker


def get_internet_search(request: Request) -> InternetSearchAdapter:
    """Return the internet search adapter from application state."""
    return request.app.state.internet_search


def get_propagation_engine(request: Request) -> PropagationEngine:
    """Return the propagation engine from application state."""
    return request.app.state.propagation_engine


def get_pipeline(request: Request) -> RAGPipeline:
    """Return the RAG pipeline from application state."""
    return request.app.state.pipeline


def get_logger_dependency():
    """Return a logger named for the API layer."""
    return get_logger("api")


SettingsDep = Annotated[Settings, Depends(get_settings)]
RepoDep = Annotated[SimpleRepository, Depends(get_repo)]
VectorStoreDep = Annotated[VectorStore, Depends(get_vector_store)]
LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]
GraphStoreDep = Annotated[Optional[GraphStore], Depends(get_graph_store)]
ChunkerDep = Annotated[DocumentChunker, Depends(get_chunker)]
RerankerDep = Annotated[Reranker, Depends(get_reranker)]
InternetSearchDep = Annotated[InternetSearchAdapter, Depends(get_internet_search)]
PropagationEngineDep = Annotated[PropagationEngine, Depends(get_propagation_engine)]
PipelineDep = Annotated[RAGPipeline, Depends(get_pipeline)]
LoggerDep = Annotated[object, Depends(get_logger_dependency)]
