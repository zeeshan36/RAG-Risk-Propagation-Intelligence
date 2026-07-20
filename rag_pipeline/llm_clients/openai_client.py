"""OpenAI LLM client adapter."""
from rag_pipeline.llm_clients.openai_compatible_client import (
    OpenAICompatibleLLMClient,
)


class OpenAILLMClient(OpenAICompatibleLLMClient):
    """Calls the OpenAI chat completions API.

    Requires the optional `openai` dependency and a valid API key.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.0,
        max_tokens: int = 2048,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            base_url=base_url,
            provider="openai",
        )
