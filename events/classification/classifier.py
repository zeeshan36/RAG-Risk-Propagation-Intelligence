"""Event classification."""
from typing import Any, Dict, Optional

from pydantic import TypeAdapter, ValidationError

from common.exceptions import EventProcessingError
from models.events import Event
from rag_pipeline.llm_clients.base import LLMClient

_event_adapter = TypeAdapter(Event)


def classify_event(
    raw: Dict[str, Any],
    llm_client: Optional[LLMClient] = None,
) -> Event:
    """Classify a raw event dictionary into the canonical Event union.

    First attempts rule-based validation via Pydantic. If that fails and an LLM
    client is provided, a simple LLM fallback is used to coerce the type field.
    """
    try:
        return _event_adapter.validate_python(raw)
    except ValidationError as exc:
        if llm_client is None:
            raise EventProcessingError(
                f"Could not classify event: {exc.errors()}"
            ) from exc
        coerced = _llm_coerce_type(raw, llm_client)
        try:
            return _event_adapter.validate_python(coerced)
        except ValidationError as exc2:
            raise EventProcessingError(
                f"LLM fallback also failed to classify event: {exc2.errors()}"
            ) from exc2


def _llm_coerce_type(raw: Dict[str, Any], llm_client: LLMClient) -> Dict[str, Any]:
    prompt = (
        "Map the following supply-chain disruption to one of these exact types: "
        "PortClosure, ExtremeWeather, CyberIncident, ExportControl, PoliticalUnrest. "
        "Return only the JSON event with the correct 'type' field and all original fields.\n\n"
        f"{raw}"
    )
    # In a real system this would parse the LLM JSON response.
    # For safety we only update the type if the LLM returns a known value.
    response = llm_client.generate(prompt)
    for known in ("PortClosure", "ExtremeWeather", "CyberIncident", "ExportControl", "PoliticalUnrest"):
        if known in response:
            return {**raw, "type": known}
    return raw
