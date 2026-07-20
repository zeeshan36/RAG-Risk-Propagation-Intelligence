"""Canonical supply-chain domain models."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FacilityType(str, Enum):
    WAREHOUSE = "warehouse"
    FACTORY = "factory"
    DC = "dc"


class RouteMode(str, Enum):
    SEA = "sea"
    AIR = "air"
    ROAD = "road"
    RAIL = "rail"


class ShipmentStatus(str, Enum):
    PLANNED = "planned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    DELAYED = "delayed"


class Region(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str


class Supplier(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    country: str
    criticality_score: float = Field(ge=0.0, le=1.0)


class Facility(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    type: FacilityType
    name: str
    region_id: str
    lat: Optional[float] = None
    lon: Optional[float] = None


class Port(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    region_id: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    modes: List[RouteMode] = Field(default_factory=list)


class Route(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    origin_node_id: str
    destination_node_id: str
    mode: RouteMode
    avg_lead_time_days: int = Field(ge=1)
    capacity: int = Field(ge=1)


class Material(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    restricted_flag: bool = False


class Product(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    sku: str
    bom_material_ids: List[str] = Field(default_factory=list)


class Customer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    region_id: str
    criticality_score: float = Field(ge=0.0, le=1.0)


class Order(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    customer_id: str
    product_id: str
    quantity: int = Field(ge=1)
    order_date: Optional[date] = None
    promised_delivery_date: Optional[date] = None
    revenue: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    margin: Decimal = Field(default=Decimal("0.00"), decimal_places=2)


class Shipment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    order_id: str
    route_ids: List[str] = Field(default_factory=list)
    carrier_id: str
    depart_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    status: ShipmentStatus = ShipmentStatus.PLANNED


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    customer_id: Optional[str] = None
    carrier_id: Optional[str] = None
    sla_days: int = Field(default=7, ge=1)
    penalty_per_day: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    force_majeure_clause: bool = False


class RevenueStream(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    order_id: str
    amount: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    margin: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    period: Optional[str] = None
