"""Graph store adapters."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from graph.schema.ontology import EdgeType, NodeType


class GraphStore(ABC):
    """Abstract interface for a property graph store."""

    @abstractmethod
    def add_node(self, node_type: NodeType, node_id: str, **props: Any) -> None:
        """Add or update a node."""

    def upsert_node(self, node_type: NodeType, node_id: str, **props: Any) -> None:
        """Alias for ``add_node`` to make incremental updates explicit."""
        self.add_node(node_type, node_id, **props)

    @abstractmethod
    def remove_node(self, node_id: str) -> bool:
        """Remove a node and its edges. Return True if it existed."""

    @abstractmethod
    def add_edge(
        self,
        edge_type: EdgeType,
        source_id: str,
        target_id: str,
        **props: Any,
    ) -> None:
        """Add or update a directed edge."""

    def upsert_edge(
        self,
        edge_type: EdgeType,
        source_id: str,
        target_id: str,
        **props: Any,
    ) -> None:
        """Alias for ``add_edge`` to make incremental updates explicit."""
        self.add_edge(edge_type, source_id, target_id, **props)

    @abstractmethod
    def remove_edge(
        self,
        edge_type: EdgeType,
        source_id: str,
        target_id: str,
    ) -> bool:
        """Remove a directed edge. Return True if it existed."""

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Return a node by ID or None."""

    @abstractmethod
    def get_neighbors(
        self,
        node_id: str,
        edge_type: Optional[EdgeType] = None,
        direction: str = "out",
    ) -> List[Tuple[EdgeType, Dict[str, Any]]]:
        """Return (edge_type, neighbor_node) tuples."""

    @abstractmethod
    def clear(self) -> None:
        """Delete all nodes and edges."""


class InMemoryGraphStore(GraphStore):
    """In-memory graph store for unit tests and minimal-mode mocks."""

    def __init__(self) -> None:
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    def add_node(self, node_type: NodeType, node_id: str, **props: Any) -> None:
        self._nodes[node_id] = {
            "type": node_type,
            "id": node_id,
            "properties": props,
        }

    def remove_node(self, node_id: str) -> bool:
        if node_id not in self._nodes:
            return False
        del self._nodes[node_id]
        self._edges = {
            key: edge
            for key, edge in self._edges.items()
            if edge["source"] != node_id and edge["target"] != node_id
        }
        return True

    def add_edge(
        self,
        edge_type: EdgeType,
        source_id: str,
        target_id: str,
        **props: Any,
    ) -> None:
        key = (edge_type.value, source_id, target_id)
        self._edges[key] = {
            "type": edge_type,
            "source": source_id,
            "target": target_id,
            "properties": props,
        }

    def remove_edge(
        self,
        edge_type: EdgeType,
        source_id: str,
        target_id: str,
    ) -> bool:
        key = (edge_type.value, source_id, target_id)
        return self._edges.pop(key, None) is not None

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        return self._nodes.get(node_id)

    def get_neighbors(
        self,
        node_id: str,
        edge_type: Optional[EdgeType] = None,
        direction: str = "out",
    ) -> List[Tuple[EdgeType, Dict[str, Any]]]:
        results: List[Tuple[EdgeType, Dict[str, Any]]] = []
        for edge in self._edges.values():
            match = False
            if direction in ("out", "both") and edge["source"] == node_id:
                match = True
                neighbor_id = edge["target"]
            elif direction in ("in", "both") and edge["target"] == node_id:
                match = True
                neighbor_id = edge["source"]
            else:
                continue
            if match and (edge_type is None or edge["type"] == edge_type):
                neighbor = self._nodes.get(neighbor_id)
                if neighbor:
                    results.append((edge["type"], neighbor))
        return results

    def clear(self) -> None:
        self._nodes.clear()
        self._edges.clear()


class Neo4jGraphStore(GraphStore):
    """Neo4j graph store adapter.

    Requires the optional `neo4j` dependency.
    """

    def __init__(self, uri: str, user: str, password: str) -> None:
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            raise ImportError(
                "Neo4jGraphStore requires neo4j to be installed "
                "(pip install rag-risk-propagation[graph])."
            ) from exc
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def add_node(self, node_type: NodeType, node_id: str, **props: Any) -> None:
        label = node_type.value
        props = dict(props, id=node_id)
        with self._driver.session() as session:
            session.run(
                f"MERGE (n:{label} {{id: $id}}) SET n += $props",
                id=node_id,
                props=props,
            )

    def remove_node(self, node_id: str) -> bool:
        with self._driver.session() as session:
            result = session.run(
                "MATCH (n {id: $id}) DETACH DELETE n RETURN count(n) AS deleted",
                id=node_id,
            ).single()
            return (result["deleted"] if result else 0) > 0

    def add_edge(
        self,
        edge_type: EdgeType,
        source_id: str,
        target_id: str,
        **props: Any,
    ) -> None:
        rel = edge_type.value
        with self._driver.session() as session:
            session.run(
                (
                    "MATCH (a {id: $source_id}), (b {id: $target_id}) "
                    f"MERGE (a)-[r:{rel}]->(b) SET r += $props"
                ),
                source_id=source_id,
                target_id=target_id,
                props=props,
            )

    def remove_edge(
        self,
        edge_type: EdgeType,
        source_id: str,
        target_id: str,
    ) -> bool:
        rel = edge_type.value
        with self._driver.session() as session:
            result = session.run(
                (
                    "MATCH (a {id: $source_id})-[r:" + rel + "]->(b {id: $target_id}) "
                    "DELETE r RETURN count(r) AS deleted"
                ),
                source_id=source_id,
                target_id=target_id,
            ).single()
            return (result["deleted"] if result else 0) > 0

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        with self._driver.session() as session:
            record = session.run(
                "MATCH (n {id: $id}) RETURN labels(n) AS labels, n AS node",
                id=node_id,
            ).single()
            if record is None:
                return None
            node = dict(record["node"])
            node["type"] = record["labels"][0]
            return node

    def get_neighbors(
        self,
        node_id: str,
        edge_type: Optional[EdgeType] = None,
        direction: str = "out",
    ) -> List[Tuple[EdgeType, Dict[str, Any]]]:
        rel_clause = ""
        params: Dict[str, Any] = {"id": node_id}
        if edge_type is not None:
            rel_clause = f"{{type: '{edge_type.value}'}}"
        if direction == "out":
            pattern = f"(n {{id: $id}})-[r{rel_clause}]->(m)"
        elif direction == "in":
            pattern = f"(n {{id: $id}})<-[r{rel_clause}]-(m)"
        else:
            pattern = f"(n {{id: $id}})-[r{rel_clause}]-(m)"

        query = f"MATCH {pattern} RETURN type(r) AS rel_type, m AS node"
        with self._driver.session() as session:
            results = []
            for record in session.run(query, **params):
                node = dict(record["node"])
                node["type"] = record["node"].labels[0]
                results.append((EdgeType(record["rel_type"]), node))
            return results

    def clear(self) -> None:
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
