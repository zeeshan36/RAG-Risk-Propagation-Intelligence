"""OpenAI LLM client adapter."""
from typing import Any, Dict

from rag_pipeline.llm_clients.base import LLMClient

try:
    import openai

    _HAS_OPENAI = True
except Exception:  # pragma: no cover
    _HAS_OPENAI = False


class OpenAILLMClient(LLMClient):
    """Calls the OpenAI chat completions API.

    Requires the optional `openai` dependency and a valid API key.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.0,
        max_tokens: int = 2048,
        api_key: str | None = None,
    ) -> None:
        if not _HAS_OPENAI:
            raise ImportError(
                "OpenAILLMClient requires openai to be installed "
                "(pip install rag-risk-propagation[llm])."
            )
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
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
        return {"provider": "openai", "model": self._model, "usage": self._last_usage}
