# RAG Risk Propagation Intelligence

A modular, config-driven GraphRAG supply-chain risk propagation system that runs in
**minimal mode** (in-memory repository + simple joins + fake LLM) and can be upgraded
to **full mode** (knowledge graph + geospatial + Kafka + real LLM/vector DB) via
config flags.

## Quick start

```bash
# Create/activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install in editable mode
pip install -e ".[dev]"

# Run the API in minimal mode
uvicorn api.main:app --reload --port 8000
```

## Configuration

Settings are loaded from `config/base.yaml` plus `config/{env}.yaml` and can be
overridden with environment variables prefixed by `RAGRP_` (use `__` for nesting).

```bash
# Use prod config
RAGRP_ENV=prod uvicorn api.main:app

# Toggle a feature via env var
RAGRP_FEATURES__USE_GRAPH_DB=true uvicorn api.main:app
RAGRP_GRAPH_DB__PROVIDER=memory uvicorn api.main:app
```

Feature flags (all default to `false` in minimal mode):

- `USE_GRAPH_DB` — use a graph store (Neo4j or in-memory) for propagation
- `USE_GEOSPATIAL` — use Shapely-backed spatial joins
- `USE_KAFKA_EVENTS` — use a Kafka consumer instead of the HTTP fallback
- `USE_SYNTHETIC_DATA` — enables synthetic-data helpers in dev
- `USE_INTERNET_SEARCH` — real internet search adapter (`NullInternetSearchAdapter` when off)
- `USE_ADVANCED_GRAPH_ALGO` — requires `USE_GRAPH_DB`
- `USE_RERANKER` — cross-encoder reranking of retrieved chunks
- `USE_CHUNKER` — heading-aware document chunking before indexing

### LLM providers

The `llm.provider` setting selects the generation backend. All real providers use
the OpenAI-compatible chat-completions API via the `openai` package.

- `fake` — deterministic canned responses, default in minimal mode
- `openai` — OpenAI (`https://api.openai.com/v1`)
- `copilot` — GitHub Copilot (`https://api.githubcopilot.com/chat/completions`)
- `kimi` — Moonshot Kimi (`https://api.moonshot.cn/v1`)
- `openrouter` — OpenRouter (`https://openrouter.ai/api/v1`)

```yaml
llm:
  provider: kimi
  model: moonshot-v1-8k
  api_key: null        # or set via env var
  base_url: null       # override the provider default if needed
```

API key resolution order: `llm.api_key` config value, then provider-specific
environment variables:

- `OPENAI_API_KEY`
- `COPILOT_API_KEY` or `GITHUB_TOKEN`
- `MOONSHOT_API_KEY`
- `OPENROUTER_API_KEY`

## API overview

- `GET /health`, `GET /ready`, `GET /metrics` — observability
- `POST /entities/{entity_type}` — ingest canonical entities
- `GET /entities/{entity_type}` — list canonical entities
- `POST /events` — ingest and classify a risk event
- `GET /events/{event_id}` — retrieve an event
- `GET /impact/{event_id}` — run propagation and return impacted entities
- `GET /analysis/{event_id}` — run the full RAG pipeline (propagation + retrieval + LLM)
- `POST /scenarios/{scenario_name}/run` — run a synthetic end-to-end scenario

Supported scenario names: `port_closure`, `extreme_weather`, `cyber_incident`,
`export_control`, `political_unrest`.

## Testing

```bash
pytest -q
```

The test suite runs without external infrastructure:

- `tests/unit/` — models, config, repository, propagation, graph, geospatial, streaming, synthetic data, pipeline
- `tests/integration/` — FastAPI endpoint tests
- `tests/e2e/` — synthetic scenario runs in minimal and mocked full (graph) modes

To run with optional dependencies installed:

```bash
pip install -e ".[all,dev]"
pytest -q
```

### No-internet test run

A dedicated offline config is provided at `config/test_minimal_no_internet.yaml`.
Run the no-internet suite with:

```bash
RAGRP_ENV=test_minimal_no_internet pytest -q tests/e2e/test_minimal_no_internet.py
```

### Chunking and reranking

- `rag_pipeline/chunking/` — `SimpleDocumentChunker` splits documents by headings and
  size, preserves tables, and attaches metadata (`source_type`, `entity_ids`,
  `effective_date`).
- `rag_pipeline/reranking/` — `NullReranker` when disabled; optional
  `CrossEncoderReranker` when `USE_RERANKER=true`.
- The RAG pipeline caps chunks sent to the LLM via `MAX_CHUNKS_PER_CALL` and logs
  before/after reranking counts.

### Incremental graph updates

`graph/builders/incremental_updates.py` provides `GraphDelta` and `apply_delta()` to
add, update, or remove nodes and edges without rebuilding the whole graph.

### Performance and stress testing

- `tests/perf/test_rag_pipeline_perf.py` — lightweight latency benchmarks for
  `analyze_event` in minimal and mocked full modes.
- `scripts/stress_test.py` — optional smoke test that fires 100 synthetic events
  against a larger network and reports avg/max latency and error count.

## Project layout

- `api/` — FastAPI app, dependencies, routers, adapter factories
- `common/` — logging, exceptions, correlation context
- `config/` — YAML config files and Pydantic loader
- `data_ingestion/batch/` — CSV/JSON loaders and in-memory repository
- `data_ingestion/mappers/` — geospatial adapters
- `data_ingestion/streaming/` — Kafka/HTTP event consumers
- `events/` — event classification and propagation engine
- `graph/` — graph schema, adapters, loaders, and queries
- `models/` — canonical domain and event models
- `rag_pipeline/` — vector stores, LLM clients, prompts, orchestration
- `synthetic_data/` — network/event generators, ground truth, scenarios
- `tests/` — unit, integration, and e2e tests
