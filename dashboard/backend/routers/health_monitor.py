"""
health_monitor.py – SQLite State & Learning API (Health Monitor)
"""

from fastapi import APIRouter, HTTPException, Query

from services import sqlite_service

router = APIRouter(prefix="/api/health", tags=["Health Monitor"])


@router.get("/logs")
async def get_logs(
    category: str | None = Query(None, description="Filter by category (e.g. LRN, TEMP, SYS)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get log entries from the short-term database."""
    try:
        logs = sqlite_service.get_logs(category=category, limit=limit, offset=offset)
        return {"count": len(logs), "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"SQLite error: {e}")


@router.get("/categories")
async def get_categories():
    """Return distinct log categories."""
    try:
        return {"categories": sqlite_service.get_log_categories()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"SQLite error: {e}")


@router.get("/state")
async def get_system_state():
    """Return all current system state key-value pairs."""
    try:
        return {"state": sqlite_service.get_state()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"SQLite error: {e}")


@router.get("/state/{key}")
async def get_state_value(key: str):
    """Return a single state value by key."""
    try:
        value = sqlite_service.get_state_value(key)
        if value is None:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
        return value
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"SQLite error: {e}")


@router.get("/mood-timeline")
async def mood_timeline(
    days: int = Query(7, ge=1, le=90),
):
    """Return mood_score time-series for the last N days."""
    try:
        return {"timeline": sqlite_service.get_mood_timeline(days=days)}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"SQLite error: {e}")


@router.get("/learning-log")
async def learning_log(
    limit: int = Query(20, ge=1, le=100),
):
    """Return the latest LRN (learning / self-improvement) entries."""
    try:
        entries = sqlite_service.get_learning_log(limit=limit)
        return {"count": len(entries), "entries": entries}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"SQLite error: {e}")
