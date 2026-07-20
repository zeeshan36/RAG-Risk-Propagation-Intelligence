"""Tests for LLM client factory dispatch."""
from unittest.mock import MagicMock

import pytest

import rag_pipeline.llm_clients.openai_compatible_client as compatible_mod
from api.factories import build_llm_client
from config.loader import LLMConfig, Settings
from rag_pipeline.llm_clients.fake_client import FakeLLMClient
from rag_pipeline.llm_clients.openai_client import OpenAILLMClient
from rag_pipeline.llm_clients.openai_compatible_client import (
    OpenAICompatibleLLMClient,
)


@pytest.fixture
def mock_openai(monkeypatch):
    """Provide a mocked openai module so tests never need the real package."""
    mock_module = MagicMock()
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.usage = {"prompt_tokens": 3, "completion_tokens": 5}
    mock_response.choices = [MagicMock(message=MagicMock(content="generated text"))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_module.OpenAI.return_value = mock_client

    monkeypatch.setattr(compatible_mod, "_HAS_OPENAI", True)
    monkeypatch.setattr(compatible_mod, "openai", mock_module)
    return mock_module


def test_factory_returns_fake_client_by_default():
    settings = Settings()
    client = build_llm_client(settings)
    assert isinstance(client, FakeLLMClient)


@pytest.mark.parametrize(
    "provider,expected_base_url",
    [
        ("openai", None),
        ("copilot", "https://api.githubcopilot.com/chat/completions"),
        ("kimi", "https://api.moonshot.cn/v1"),
        ("openrouter", "https://openrouter.ai/api/v1"),
    ],
)
def test_factory_dispatches_openai_compatible_providers(
    mock_openai, provider, expected_base_url
):
    settings = Settings(llm=LLMConfig(provider=provider))
    client = build_llm_client(settings)
    assert isinstance(client, OpenAICompatibleLLMClient)
    mock_openai.OpenAI.assert_called_once_with(api_key=None, base_url=expected_base_url)


def test_factory_openai_client_is_openai_compatible(mock_openai):
    settings = Settings(llm=LLMConfig(provider="openai"))
    client = build_llm_client(settings)
    assert isinstance(client, OpenAILLMClient)
    assert client.generation_metadata()["provider"] == "openai"


def test_factory_uses_env_api_key_fallback(mock_openai, monkeypatch):
    monkeypatch.setenv("MOONSHOT_API_KEY", "moonshot-env-key")
    settings = Settings(llm=LLMConfig(provider="kimi"))
    build_llm_client(settings)
    mock_openai.OpenAI.assert_called_once_with(
        api_key="moonshot-env-key",
        base_url="https://api.moonshot.cn/v1",
    )


def test_factory_config_api_key_overrides_env(mock_openai, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-env-key")
    settings = Settings(
        llm=LLMConfig(provider="openrouter", api_key="openrouter-cfg-key")
    )
    build_llm_client(settings)
    mock_openai.OpenAI.assert_called_once_with(
        api_key="openrouter-cfg-key",
        base_url="https://openrouter.ai/api/v1",
    )


def test_factory_base_url_override_takes_precedence(mock_openai):
    custom_url = "http://custom.llm.local/v1"
    settings = Settings(llm=LLMConfig(provider="copilot", base_url=custom_url))
    build_llm_client(settings)
    mock_openai.OpenAI.assert_called_once_with(api_key=None, base_url=custom_url)
