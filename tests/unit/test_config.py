"""Tests for configuration loading."""
import os
from pathlib import Path

import pytest

from common.exceptions import ConfigMisconfigurationError
from config.loader import LLMConfig, Settings, load_settings


@pytest.fixture
def config_dir() -> Path:
    return Path(__file__).parents[2] / "config"


def test_load_dev_defaults(config_dir: Path):
    settings = load_settings(env="dev", config_dir=config_dir)
    assert settings.app.env == "dev"
    assert settings.app.log_level == "DEBUG"
    assert settings.features.use_graph_db is False
    assert settings.features.use_synthetic_data is True
    assert settings.server.port == 8000


def test_load_prod_defaults(config_dir: Path):
    settings = load_settings(env="prod", config_dir=config_dir)
    assert settings.app.env == "prod"
    assert settings.app.log_level == "WARNING"
    assert settings.features.use_graph_db is True
    assert settings.features.use_kafka_events is True
    assert settings.server.port == 8080


def test_env_override(config_dir: Path, monkeypatch):
    monkeypatch.setenv("RAGRP_FEATURES__USE_GRAPH_DB", "true")
    settings = load_settings(env="dev", config_dir=config_dir)
    assert settings.features.use_graph_db is True


def test_invalid_advanced_graph_without_graph(config_dir: Path, monkeypatch):
    monkeypatch.setenv("RAGRP_FEATURES__USE_GRAPH_DB", "false")
    monkeypatch.setenv("RAGRP_FEATURES__USE_ADVANCED_GRAPH_ALGO", "true")
    with pytest.raises(ConfigMisconfigurationError):
        load_settings(env="dev", config_dir=config_dir)


@pytest.mark.parametrize(
    "provider",
    ["fake", "openai", "copilot", "kimi", "openrouter"],
)
def test_llm_provider_values_are_accepted(provider: str):
    settings = Settings(llm=LLMConfig(provider=provider))
    assert settings.llm.provider == provider


def test_llm_api_key_and_base_url_are_loaded():
    settings = Settings(
        llm=LLMConfig(
            provider="kimi",
            api_key="secret",
            base_url="https://custom.example.com/v1",
        )
    )
    assert settings.llm.api_key == "secret"
    assert settings.llm.base_url == "https://custom.example.com/v1"


def test_llm_api_key_and_base_url_env_override(config_dir: Path, monkeypatch):
    monkeypatch.setenv("RAGRP_LLM__PROVIDER", "openrouter")
    monkeypatch.setenv("RAGRP_LLM__API_KEY", "env-key")
    monkeypatch.setenv("RAGRP_LLM__BASE_URL", "https://env.example.com/v1")
    settings = load_settings(env="dev", config_dir=config_dir)
    assert settings.llm.provider == "openrouter"
    assert settings.llm.api_key == "env-key"
    assert settings.llm.base_url == "https://env.example.com/v1"


def test_invalid_llm_provider_is_rejected():
    with pytest.raises(ValueError):
        LLMConfig(provider="unknown")


def test_secret_connection_defaults_are_null():
    settings = Settings()
    assert settings.llm.api_key is None
    assert settings.llm.base_url is None
    assert settings.graph_db.password is None
    assert settings.internet_search.search_api_url is None
    assert settings.internet_search.api_key is None


def test_internet_search_config_env_override(config_dir: Path, monkeypatch):
    monkeypatch.setenv("RAGRP_INTERNET_SEARCH__SEARCH_API_URL", "https://search.example.com")
    monkeypatch.setenv("RAGRP_INTERNET_SEARCH__API_KEY", "search-secret")
    settings = load_settings(env="dev", config_dir=config_dir)
    assert settings.internet_search.search_api_url == "https://search.example.com"
    assert settings.internet_search.api_key == "search-secret"


def test_graph_db_password_env_override(config_dir: Path, monkeypatch):
    monkeypatch.setenv("RAGRP_GRAPH_DB__PASSWORD", "neo4j-secret")
    settings = load_settings(env="dev", config_dir=config_dir)
    assert settings.graph_db.password == "neo4j-secret"
