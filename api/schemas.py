"""API request/response schemas."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from models.events import Event


class EventIngestResponse(BaseModel):
    event_id: str
    event_type: str
    status: str = "ingested"


class EntitySummary(BaseModel):
    entity_type: str
    entity_id: str
    name: Optional[str] = None


class ImpactResponse(BaseModel):
    event_id: str
    impacted_entities: List[EntitySummary]


class ScenarioRunResponse(BaseModel):
    scenario_name: str
    status: str = "completed"
    summary: Dict[str, Any]
