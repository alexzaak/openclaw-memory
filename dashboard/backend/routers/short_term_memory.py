"""
short_term_memory.py – Daily Context & Learnings API
"""

from fastapi import APIRouter, HTTPException, Query

from services import sqlite_service

router = APIRouter(prefix="/api/memory", tags=["Short-Term Memory"])


@router.get("/daily-context")
async def get_daily_context(
    scope: str | None = Query(None, description="Filter by scope (alex, laura, family, system)"),
    limit: int = Query(50, ge=1, le=200),
):
    """Return the recent short-term memory items (daily_context)."""
    try:
        entries = sqlite_service.get_daily_context(scope=scope, limit=limit)
        return {"count": len(entries), "entries": entries}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"SQLite error: {e}")


@router.get("/learnings")
async def get_learnings(
    category: str | None = Query(None, description="Filter by category"),
    processed: bool | None = Query(None, description="Filter by processed state"),
    limit: int = Query(50, ge=1, le=200),
):
    """Return learnings from the short-term database."""
    try:
        entries = sqlite_service.get_learnings(
            category=category, processed=processed, limit=limit
        )
        return {"count": len(entries), "entries": entries}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"SQLite error: {e}")


@router.get("/learnings/categories")
async def get_learning_categories():
    """Return distinct learning categories."""
    try:
        return {"categories": sqlite_service.get_learning_categories()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"SQLite error: {e}")
