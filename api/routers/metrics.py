"""Metrics and readiness endpoints."""
from fastapi import APIRouter

from api.dependencies import GraphStoreDep, RepoDep, SettingsDep, VectorStoreDep

router = APIRouter(tags=["metrics"])


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.get("/ready")
def readiness_check(repo: RepoDep, vector_store: VectorStoreDep):
    return {
        "status": "ready",
        "entity_types": repo.type_count(),
        "vector_documents": vector_store.count(),
    }


@router.get("/metrics")
def metrics_check(repo: RepoDep, vector_store: VectorStoreDep, settings: SettingsDep, graph_store: GraphStoreDep):
    return {
        "entity_types": repo.type_count(),
        "total_entities": repo.total_count(),
        "vector_documents": vector_store.count(),
        "features": settings.features.model_dump(),
        "graph_store_enabled": graph_store is not None,
    }
