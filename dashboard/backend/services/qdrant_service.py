"""
qdrant_service.py – Qdrant Vector DB Service
"""

import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION

log = logging.getLogger("qdrant_service")

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    return _client


def semantic_search(
    query_vector: list[float],
    limit: int = 20,
    sender_filter: str | None = None,
) -> list[dict]:
    """Perform semantic search on the openclaw_memory collection."""
    client = get_client()

    search_filter = None
    if sender_filter:
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="sender",
                    match=MatchValue(value=sender_filter),
                )
            ]
        )

    results = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        query_filter=search_filter,
        limit=limit,
        with_payload=True,
    )

    return [
        {
            "id": str(point.id),
            "score": round(point.score, 4),
            "text": point.payload.get("text", ""),
            "sender": point.payload.get("sender", "unknown"),
            "timestamp": point.payload.get("timestamp", ""),
            "session_id": point.payload.get("session_id", ""),
        }
        for point in results.points
    ]


def scroll_recent(limit: int = 50, offset: str | None = None) -> dict:
    """Scroll through memory points chronologically."""
    client = get_client()

    results, next_offset = client.scroll(
        collection_name=QDRANT_COLLECTION,
        limit=limit,
        offset=offset,
        with_payload=True,
        with_vectors=False,
        order_by="timestamp",
    )

    points = [
        {
            "id": str(point.id),
            "text": point.payload.get("text", ""),
            "sender": point.payload.get("sender", "unknown"),
            "timestamp": point.payload.get("timestamp", ""),
            "session_id": point.payload.get("session_id", ""),
        }
        for point in results
    ]

    return {
        "points": points,
        "next_offset": str(next_offset) if next_offset else None,
    }


def get_collection_info() -> dict:
    """Return collection statistics."""
    client = get_client()
    try:
        info = client.get_collection(QDRANT_COLLECTION)
        return {
            "name": QDRANT_COLLECTION,
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "status": str(info.status),
        }
    except Exception as e:
        log.error("Failed to get collection info: %s", e)
        return {"name": QDRANT_COLLECTION, "error": str(e)}
