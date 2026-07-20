"""Pydantic-based configuration loader."""
import os
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import yaml
from pydantic import BaseModel, Field, model_validator

from common.exceptions import ConfigMisconfigurationError


class AppConfig(BaseModel):
    name: str = "rag-risk-propagation"
    env: str = "dev"
    log_level: str = "INFO"


class FeatureFlags(BaseModel):
    use_graph_db: bool = False
    use_geospatial: bool = False
    use_kafka_events: bool = False
    use_synthetic_data: bool = False
    use_internet_search: bool = False
    use_advanced_graph_algo: bool = False
    use_reranker: bool = False
    use_chunker: bool = False


class VectorStoreConfig(BaseModel):
    provider: Literal["chroma", "memory", "none"] = "memory"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    collection_name: str = "supply_chain_docs"
    persist_directory: str = "./data/chroma"


class LLMConfig(BaseModel):
    provider: Literal["fake", "openai", "copilot", "kimi", "openrouter"] = "fake"
    model: str = "gpt-4o"
    temperature: float = 0.0
    max_tokens: int = 2048
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class GraphDBConfig(BaseModel):
    provider: Literal["neo4j", "memory"] = "neo4j"
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: Optional[str] = None


class InternetSearchConfig(BaseModel):
    search_api_url: Optional[str] = None
    api_key: Optional[str] = None


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class RerankerConfig(BaseModel):
    use_reranker: bool = False
    model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    top_k: int = 5


class ChunkingConfig(BaseModel):
    use_chunker: bool = False
    max_chunk_size: int = 512
    preserve_tables: bool = True
    heading_regex: str = r"^#{1,3}\s+"


class Settings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    graph_db: GraphDBConfig = Field(default_factory=GraphDBConfig)
    internet_search: InternetSearchConfig = Field(default_factory=InternetSearchConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    reranker: RerankerConfig = Field(default_factory=RerankerConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    max_chunks_per_call: int = 10

    @model_validator(mode="after")
    def check_consistency(self) -> "Settings":
        if self.features.use_advanced_graph_algo and not self.features.use_graph_db:
            raise ConfigMisconfigurationError(
                "USE_ADVANCED_GRAPH_ALGO requires USE_GRAPH_DB to be enabled."
            )
        if self.features.use_graph_db and self.graph_db.provider == "neo4j":
            # Neo4j password should be supplied via config or RAGRP_GRAPH_DB__PASSWORD.
            pass
        return self

    def is_feature_enabled(self, flag_name: str) -> bool:
        return bool(getattr(self.features, flag_name, False))


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _env_overrides() -> Dict[str, Any]:
    """Build a nested dict from environment variables prefixed with RAGRP_."""
    overrides: Dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith("RAGRP_"):
            continue
        parts = key[6:].lower().split("__")
        current: Dict[str, Any] = overrides
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = _coerce(value)
    return overrides


def _coerce(value: str) -> Any:
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def load_settings(
    env: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> Settings:
    """Load settings from base + env YAML files and environment variables."""
    config_dir = config_dir or Path(__file__).parent
    env = env or os.getenv("RAGRP_ENV", "dev")

    base_path = config_dir / "base.yaml"
    env_path = config_dir / f"{env}.yaml"

    data: Dict[str, Any] = {}
    for path in (base_path, env_path):
        if path.exists():
            with open(path, "r", encoding="utf-8") as fh:
                data = _deep_merge(data, yaml.safe_load(fh) or {})

    data = _deep_merge(data, _env_overrides())
    data.setdefault("app", {})["env"] = env
    return Settings.model_validate(data)
