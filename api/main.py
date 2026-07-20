"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.factories import (
    build_chunker,
    build_geo_mapper,
    build_graph_store,
    build_internet_search,
    build_llm_client,
    build_pipeline,
    build_propagation_engine,
    build_reranker,
    build_vector_store,
    seed_vector_store,
)
from api.routers import entities, events, metrics, scenarios
from common.context import correlation_context, get_correlation_id
from common.logging import get_logger, setup_logging
from config.loader import load_settings
from data_ingestion.batch.simple_repository import SimpleRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    setup_logging(settings.app.log_level)
    logger = get_logger("api.main")
    app.state.settings = settings
    app.state.repo = SimpleRepository()
    app.state.vector_store = build_vector_store(settings)
    app.state.llm_client = build_llm_client(settings)
    app.state.geo_mapper = build_geo_mapper(settings)
    app.state.graph_store = build_graph_store(settings)
    app.state.chunker = build_chunker(settings)
    app.state.reranker = build_reranker(settings)
    app.state.internet_search = build_internet_search(settings)
    if app.state.graph_store is not None:
        from graph.loaders.builder import load_repository_into_graph

        load_repository_into_graph(app.state.repo, app.state.graph_store)
    app.state.propagation_engine = build_propagation_engine(
        settings,
        app.state.repo,
        app.state.graph_store,
        app.state.geo_mapper,
    )
    app.state.pipeline = build_pipeline(
        app.state.repo,
        app.state.vector_store,
        app.state.llm_client,
        app.state.propagation_engine,
        app.state.reranker,
        app.state.internet_search,
        settings,
    )
    seed_vector_store(app.state.repo, app.state.vector_store, app.state.chunker)
    logger.info(
        "Application starting",
        extra={
            "env": settings.app.env,
            "graph_enabled": settings.features.use_graph_db,
            "vector_provider": settings.vector_store.provider,
        },
    )
    yield
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG Risk Propagation",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next):
        cid = request.headers.get("x-correlation-id") or get_correlation_id()
        with correlation_context(cid):
            response = await call_next(request)
            response.headers["x-correlation-id"] = cid
            return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger = get_logger("api.main")
        logger.exception("Unhandled exception", extra={"request_path": request.url.path})
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    app.include_router(metrics.router)
    app.include_router(entities.router)
    app.include_router(events.router)
    app.include_router(scenarios.router)
    return app


app = create_app()
