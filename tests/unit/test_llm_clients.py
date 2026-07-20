"""Tests for LLM client adapters."""
import pytest

from rag_pipeline.llm_clients.fake_client import FakeLLMClient
from rag_pipeline.llm_clients.openai_client import OpenAILLMClient


def test_fake_llm_client_default_response():
    client = FakeLLMClient()
    response = client.generate("What is the impact?")
    assert "fake llm response" in response.lower()


def test_fake_llm_client_custom_response():
    client = FakeLLMClient(responses={"impact": "Severe disruption expected."})
    response = client.generate("Please assess the impact.")
    assert response == "Severe disruption expected."


def test_openai_client_requires_dependency():
    try:
        import openai  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError):
            OpenAILLMClient(api_key="test")
