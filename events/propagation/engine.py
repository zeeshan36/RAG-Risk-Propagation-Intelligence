"""Propagation engine that dispatches to rule-based or graph traversal logic."""
from typing import TYPE_CHECKING, Optional

from events.propagation import rules
from events.propagation.impact_result import ImpactResult
from models.events import (
    CyberIncident,
    Event,
    ExportControl,
    ExtremeWeather,
    PoliticalUnrest,
    PortClosure,
)

if TYPE_CHECKING:
    from data_ingestion.batch.simple_repository import SimpleRepository


class PropagationEngine:
    """Dispatches propagation to the right backend."""

    def __init__(
        self,
        repo: "SimpleRepository",
        graph_store: Optional[object] = None,
        geo_mapper: Optional[object] = None,
        use_graph: bool = False,
    ) -> None:
        self.repo = repo
        self.graph_store = graph_store
        self.geo_mapper = geo_mapper
        self.use_graph = use_graph and graph_store is not None

    def propagate(self, event: Event) -> ImpactResult:
        """Run propagation for the given event."""
        if self.use_graph:
            return self._propagate_with_graph(event)
        return self._propagate_rules(event)

    def _propagate_rules(self, event: Event) -> ImpactResult:
        if isinstance(event, PortClosure):
            return rules.propagate_port_closure(event, self.repo)
        if isinstance(event, ExtremeWeather):
            return rules.propagate_extreme_weather(event, self.repo, self.geo_mapper)
        if isinstance(event, CyberIncident):
            return rules.propagate_cyber_incident(event, self.repo)
        if isinstance(event, ExportControl):
            return rules.propagate_export_control(event, self.repo)
        if isinstance(event, PoliticalUnrest):
            return rules.propagate_political_unrest(event, self.repo)
        raise ValueError(f"Unsupported event type: {event.type}")

    def _propagate_with_graph(self, event: Event) -> ImpactResult:
        # Delegated to the graph query module once implemented.
        from graph.queries import impact_paths

        return impact_paths.propagate_event(self.graph_store, event, self.repo)
