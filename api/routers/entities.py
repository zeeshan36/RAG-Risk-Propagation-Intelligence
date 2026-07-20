"""Canonical entity ingestion endpoints."""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import TypeAdapter

from api.dependencies import LoggerDep, RepoDep
from models.domain import (
    Contract,
    Customer,
    Facility,
    Material,
    Order,
    Port,
    Product,
    Region,
    RevenueStream,
    Route,
    Shipment,
    Supplier,
)
from models.events import Event

router = APIRouter(tags=["entities"])

_ENTITY_TYPES: Dict[str, Any] = {
    "region": Region,
    "supplier": Supplier,
    "facility": Facility,
    "port": Port,
    "material": Material,
    "product": Product,
    "customer": Customer,
    "route": Route,
    "order": Order,
    "shipment": Shipment,
    "contract": Contract,
    "revenue_stream": RevenueStream,
}


@router.post("/entities/{entity_type}")
def ingest_entity(entity_type: str, payload: Dict[str, Any], repo: RepoDep, logger: LoggerDep):
    """Ingest a single canonical entity."""
    model_cls = _ENTITY_TYPES.get(entity_type)
    if model_cls is None:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {entity_type}")
    entity = TypeAdapter(model_cls).validate_python(payload)
    repo.upsert(entity)
    logger.info("Ingested entity", extra={"entity_type": entity_type, "entity_id": entity.id})
    return {"entity_id": entity.id, "entity_type": entity_type, "status": "ingested"}


@router.get("/entities/{entity_type}")
def list_entities(entity_type: str, repo: RepoDep):
    model_cls = _ENTITY_TYPES.get(entity_type)
    if model_cls is None:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {entity_type}")
    return [e.model_dump() for e in repo.list(model_cls)]
