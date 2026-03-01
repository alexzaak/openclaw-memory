"""
knowledge_vault.py – FalkorDB Entity Explorer API (Knowledge Vault)
"""

from fastapi import APIRouter, HTTPException, Query

from services import falkor_service

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Vault"])


@router.get("/entities")
async def list_entities(
    label: str | None = Query(None, description="Filter by node label (Person, Project, Task, …)"),
    search: str | None = Query(None, description="Search by name"),
    limit: int = Query(50, ge=1, le=200),
):
    """List entities from the knowledge graph."""
    try:
        entities = falkor_service.get_entities(
            label=label, search=search, limit=limit,
        )
        return {"count": len(entities), "entities": entities}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"FalkorDB error: {e}")


@router.get("/entities/{node_id}")
async def entity_detail(node_id: int):
    """Get full entity detail with all connections."""
    try:
        entity = falkor_service.get_entity_detail(node_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="Entity not found")
        return entity
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"FalkorDB error: {e}")


@router.get("/stats")
async def graph_stats():
    """Return knowledge graph statistics (node/edge counts, label distribution)."""
    try:
        return falkor_service.get_graph_stats()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"FalkorDB error: {e}")
