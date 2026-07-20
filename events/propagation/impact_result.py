"""Result model for propagation analysis."""
from typing import List, Optional

from pydantic import BaseModel


class ImpactedEntity(BaseModel):
    entity_type: str
    entity_id: str
    name: Optional[str] = None


class ImpactResult(BaseModel):
    event_id: str
    event_type: str
    impacted_entities: List[ImpactedEntity] = []
    impacted_shipment_ids: List[str] = []
    impacted_order_ids: List[str] = []
    impacted_customer_ids: List[str] = []
    impacted_product_ids: List[str] = []
    impacted_route_ids: List[str] = []
    impacted_facility_ids: List[str] = []
    estimated_revenue_at_risk: float = 0.0

    def add(self, entity_type: str, entity_id: str, name: Optional[str] = None) -> None:
        if not any(
            e.entity_type == entity_type and e.entity_id == entity_id
            for e in self.impacted_entities
        ):
            self.impacted_entities.append(
                ImpactedEntity(entity_type=entity_type, entity_id=entity_id, name=name)
            )
