"""Event ingestion and impact endpoints."""
from typing import List, Type

from fastapi import APIRouter, HTTPException

from api.dependencies import (
    LoggerDep,
    PipelineDep,
    PropagationEngineDep,
    RepoDep,
)
from api.schemas import EntitySummary, EventIngestResponse, ImpactResponse
from models.events import CyberIncident, Event, ExportControl, ExtremeWeather, PoliticalUnrest, PortClosure

router = APIRouter(tags=["events"])

_EVENT_TYPES: List[Type[Event]] = [
    PortClosure,
    ExtremeWeather,
    CyberIncident,
    ExportControl,
    PoliticalUnrest,
]


@router.post("/events", response_model=EventIngestResponse)
def ingest_event(payload: Event, repo: RepoDep, logger: LoggerDep):
    """Ingest and classify a supply-chain risk event."""
    logger.info("Ingesting event", extra={"event_id": payload.id, "event_type": payload.type})
    repo.upsert(payload)
    return EventIngestResponse(event_id=payload.id, event_type=payload.type)


@router.get("/events/{event_id}")
def get_event(event_id: str, repo: RepoDep):
    """Retrieve an event by ID."""
    for event_cls in _EVENT_TYPES:
        try:
            return repo.get(event_cls, event_id)
        except Exception:
            continue
    raise HTTPException(status_code=404, detail=f"Event {event_id} not found")


@router.get("/impact/{event_id}", response_model=ImpactResponse)
def get_impact(event_id: str, repo: RepoDep, engine: PropagationEngineDep):
    """Run propagation analysis for an event."""
    event = None
    for event_cls in _EVENT_TYPES:
        try:
            event = repo.get(event_cls, event_id)
            break
        except Exception:
            continue
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    impact = engine.propagate(event)
    entities = [
        EntitySummary(**entity.model_dump()) for entity in impact.impacted_entities
    ]
    return ImpactResponse(
        event_id=event_id,
        impacted_entities=entities,
    )


@router.get("/analysis/{event_id}")
def analyze_event(event_id: str, pipeline: PipelineDep):
    """Run the full RAG analysis pipeline for an event."""
    try:
        return pipeline.analyze_event(event_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
