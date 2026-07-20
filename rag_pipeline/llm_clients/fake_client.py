"""Fake LLM client for tests and minimal mode."""
from typing import Any, Dict

from rag_pipeline.llm_clients.base import LLMClient


class FakeLLMClient(LLMClient):
    """Returns deterministic canned text; never calls an external API."""

    def __init__(self, responses: Dict[str, str] | None = None) -> None:
        self._responses = responses or {}
        self._default = (
            "This is a fake LLM response. No external service was called."
        )
        self._last_prompt: str | None = None

    def generate(self, prompt: str, **kwargs: Any) -> str:
        self._last_prompt = prompt
        for key, response in self._responses.items():
            if key.lower() in prompt.lower():
                return response
        return self._default

    def generation_metadata(self) -> Dict[str, Any]:
        return {"provider": "fake", "last_prompt_length": len(self._last_prompt or "")}
