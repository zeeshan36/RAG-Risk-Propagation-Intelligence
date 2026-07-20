"""Tests for LLM client adapters."""
from unittest.mock import MagicMock

import pytest

import rag_pipeline.llm_clients.openai_compatible_client as compatible_mod
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


def test_fake_llm_client_default_response():
    client = FakeLLMClient()
    response = client.generate("What is the impact?")
    assert "fake llm response" in response.lower()


def test_fake_llm_client_custom_response():
    client = FakeLLMClient(responses={"impact": "Severe disruption expected."})
    response = client.generate("Please assess the impact.")
    assert response == "Severe disruption expected."


def test_openai_client_requires_dependency(monkeypatch):
    monkeypatch.setattr(compatible_mod, "_HAS_OPENAI", False)
    with pytest.raises(ImportError):
        OpenAILLMClient(api_key="test")


@pytest.mark.parametrize("provider", ["openai", "copilot", "kimi", "openrouter"])
def test_compatible_client_records_provider_metadata(mock_openai, provider):
    client = OpenAICompatibleLLMClient(provider=provider)
    assert client.generation_metadata()["provider"] == provider


def test_compatible_client_uses_supplied_base_url(mock_openai):
    custom_url = "http://localhost:9999/v1"
    OpenAICompatibleLLMClient(provider="openai", base_url=custom_url)
    mock_openai.OpenAI.assert_called_once_with(api_key=None, base_url=custom_url)


def test_compatible_client_generate_returns_content(mock_openai):
    client = OpenAICompatibleLLMClient(provider="kimi", api_key="secret")
    result = client.generate("Analyze this event")
    assert result == "generated text"
    mock_openai.OpenAI.return_value.chat.completions.create.assert_called_once()
    assert client.generation_metadata()["usage"] == {
        "prompt_tokens": 3,
        "completion_tokens": 5,
    }


def test_openai_client_reports_provider_openai(mock_openai):
    client = OpenAILLMClient(api_key="test")
    assert client.generation_metadata()["provider"] == "openai"
