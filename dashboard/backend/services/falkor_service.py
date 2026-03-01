"""
falkor_service.py – FalkorDB Knowledge Graph Service
"""

import logging
from typing import Any
from falkordb import FalkorDB
from config import FALKOR_HOST, FALKOR_PORT, FALKOR_GRAPH

log = logging.getLogger("falkor_service")

_db: FalkorDB | None = None


def get_graph():
    global _db
    if _db is None:
        _db = FalkorDB(host=FALKOR_HOST, port=FALKOR_PORT)
    return _db.select_graph(FALKOR_GRAPH)


def _node_to_dict(node, label: str | None = None) -> dict:
    """Convert a FalkorDB node to a JSON-serializable dict."""
    return {
        "id": node.id,
        "label": label or "",
        "properties": {k: v for k, v in node.properties.items()},
    }


def get_entities(
    label: str | None = None,
    search: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """List entities, optional label filter and name search."""
    graph = get_graph()

    if label:
        cypher = f"MATCH (n:{label}) RETURN n, labels(n)[0] LIMIT {limit}"
    else:
        cypher = f"MATCH (n) RETURN n, labels(n)[0] LIMIT {limit}"

    results = graph.query(cypher).result_set

    entities = []
    for record in results:
        node = record[0]
        node_label = record[1]
        entity = _node_to_dict(node, node_label)

        # Get connection count
        conn_result = graph.query(
            f"MATCH (n)-[r]-(m) WHERE id(n) = {node.id} RETURN count(r)"
        ).result_set
        entity["connection_count"] = conn_result[0][0] if conn_result else 0

        # Apply name search filter (client-side for FalkorDB compatibility)
        if search:
            name = entity["properties"].get("name", "")
            if search.lower() not in name.lower():
                continue

        entities.append(entity)

    return entities


def get_entity_detail(node_id: int) -> dict | None:
    """Get full entity detail with connected entities."""
    graph = get_graph()

    # Get the node itself
    node_result = graph.query(
        f"MATCH (n) WHERE id(n) = {node_id} RETURN n, labels(n)[0]"
    ).result_set

    if not node_result:
        return None

    node = node_result[0][0]
    label = node_result[0][1]
    entity = _node_to_dict(node, label)

    # Get all connected entities with relationship info
    rel_result = graph.query(f"""
        MATCH (n)-[r]-(m)
        WHERE id(n) = {node_id}
        RETURN m, labels(m)[0], type(r), startNode(r) = n
    """).result_set

    connections = []
    for record in rel_result:
        connected_node = record[0]
        connected_label = record[1]
        rel_type = record[2]
        is_outgoing = record[3]

        connections.append({
            "node": _node_to_dict(connected_node, connected_label),
            "relationship": rel_type,
            "direction": "outgoing" if is_outgoing else "incoming",
        })

    entity["connections"] = connections
    return entity


def get_graph_stats() -> dict:
    """Return graph statistics: node/edge counts, label distribution."""
    graph = get_graph()

    try:
        node_count = graph.query("MATCH (n) RETURN count(n)").result_set[0][0]
        edge_count = graph.query(
            "MATCH ()-[r]->() RETURN count(r)"
        ).result_set[0][0]

        # Label distribution
        label_result = graph.query(
            "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY cnt DESC"
        ).result_set

        labels = {record[0]: record[1] for record in label_result}

        # Relationship type distribution
        rel_result = graph.query(
            "MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS cnt ORDER BY cnt DESC"
        ).result_set

        relationships = {record[0]: record[1] for record in rel_result}

        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "labels": labels,
            "relationship_types": relationships,
        }
    except Exception as e:
        log.error("Failed to get graph stats: %s", e)
        return {"error": str(e)}
