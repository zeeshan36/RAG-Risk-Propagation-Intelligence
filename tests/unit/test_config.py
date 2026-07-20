"""Tests for configuration loading."""
import os
from pathlib import Path

import pytest

from common.exceptions import ConfigMisconfigurationError
from config.loader import Settings, load_settings


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
