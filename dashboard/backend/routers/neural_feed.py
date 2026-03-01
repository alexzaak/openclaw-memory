"""
neural_feed.py – Qdrant Explorer API (Neural Feed)
"""

from fastapi import APIRouter, HTTPException, Query

from services import embedding_service, qdrant_service

router = APIRouter(prefix="/api/neural-feed", tags=["Neural Feed"])


@router.get("/search")
async def search_memories(
    q: str = Query(..., min_length=1, description="Semantic search query"),
    limit: int = Query(20, ge=1, le=100),
    sender: str | None = Query(None, description="Filter by sender (user/assistant)"),
):
    """Embed the query via Ollama, then search Qdrant for similar memories."""
    vector = embedding_service.get_embedding(q)
    if vector is None:
        raise HTTPException(
            status_code=503,
            detail="Embedding service (Ollama) is not available.",
        )

    results = qdrant_service.semantic_search(
        query_vector=vector,
        limit=limit,
        sender_filter=sender,
    )
    return {"query": q, "count": len(results), "results": results}


@router.get("/recent")
async def recent_memories(
    limit: int = Query(50, ge=1, le=200),
    offset: str | None = Query(None, description="Pagination offset token"),
):
    """Scroll through memories chronologically (newest first)."""
    try:
        data = qdrant_service.scroll_recent(limit=limit, offset=offset)
        return data
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Qdrant error: {e}")


@router.get("/stats")
async def collection_stats():
    """Return Qdrant collection statistics."""
    return qdrant_service.get_collection_info()
