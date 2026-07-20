"""Abstract LLM client interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMClient(ABC):
    """Adapter interface for LLM text generation."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a text completion for the given prompt."""

    def generation_metadata(self) -> Dict[str, Any]:
        """Return metadata about the last generation if available."""
        return {}
