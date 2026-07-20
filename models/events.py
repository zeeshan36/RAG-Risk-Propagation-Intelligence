"""Event ontology models."""
from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EventBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    type: str
    start_time: Optional[datetime] = None
    expected_duration_hours: int = Field(default=24, ge=0)
    severity: Severity = Severity.MEDIUM
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    data_source: Optional[str] = None


class PortClosure(EventBase):
    type: Literal["PortClosure"] = "PortClosure"
    port_id: str
    affected_operations: str = "full"
    impacted_modes: List[str] = Field(default_factory=list)


class ExtremeWeather(EventBase):
    type: Literal["ExtremeWeather"] = "ExtremeWeather"
    hazard_type: str
    center_lat: float
    center_lon: float
    radius_deg: float = Field(gt=0.0)


class CyberIncident(EventBase):
    type: Literal["CyberIncident"] = "CyberIncident"
    provider_id: str
    impacted_systems: List[str] = Field(default_factory=list)
    functional_impact: Optional[str] = None


class ExportControl(EventBase):
    type: Literal["ExportControl"] = "ExportControl"
    material_id: str
    country: Optional[str] = None
    restriction_type: str = "ban"


class PoliticalUnrest(EventBase):
    type: Literal["PoliticalUnrest"] = "PoliticalUnrest"
    region_id: str
    impacted_sectors: List[str] = Field(default_factory=list)


Event = Union[PortClosure, ExtremeWeather, CyberIncident, ExportControl, PoliticalUnrest]
