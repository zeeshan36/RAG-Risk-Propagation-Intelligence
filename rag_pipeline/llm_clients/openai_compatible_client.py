"""OpenAI-compatible LLM client adapter.

Supports any provider that exposes the OpenAI chat-completions API,
including GitHub Copilot, Moonshot Kimi, and OpenRouter.
"""
from typing import Any, Dict

from rag_pipeline.llm_clients.base import LLMClient

try:
    import openai

    _HAS_OPENAI = True
except Exception:  # pragma: no cover
    openai = None  # type: ignore[assignment]
    _HAS_OPENAI = False


class OpenAICompatibleLLMClient(LLMClient):
    """Calls an OpenAI-compatible chat completions endpoint.

    Requires the optional `openai` dependency and a valid API key for the
    chosen provider.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.0,
        max_tokens: int = 2048,
        api_key: str | None = None,
        base_url: str | None = None,
        provider: str = "openai-compatible",
    ) -> None:
        if not _HAS_OPENAI:
            raise ImportError(
                "OpenAICompatibleLLMClient requires openai to be installed "
                "(pip install rag-risk-propagation[llm])."
            )
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._provider = provider
        self._base_url = base_url
        self._last_usage: Dict[str, Any] = {}

    def generate(self, prompt: str, **kwargs: Any) -> str:
        response = self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            temperature=kwargs.get("temperature", self._temperature),
            max_tokens=kwargs.get("max_tokens", self._max_tokens),
            messages=[{"role": "user", "content": prompt}],
        )
        self._last_usage = dict(response.usage) if response.usage else {}
        return response.choices[0].message.content or ""

    def generation_metadata(self) -> Dict[str, Any]:
        return {
            "provider": self._provider,
            "model": self._model,
            "base_url": self._base_url,
            "usage": self._last_usage,
        }
