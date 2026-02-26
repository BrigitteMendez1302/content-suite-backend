"""Brand management endpoints.

Provides CRUD operations for brands and brand manual generation.
All business logic delegated to service layer.
"""
from fastapi import APIRouter, HTTPException

from app.db.supabase_client import get_supabase
from app.models.brand import BrandCreateRequest, BrandCreateResponse
from app.services.brand_manual import create_brand_manual
from app.repositories import brand_manual as manual_repo

router = APIRouter(prefix="/brands", tags=["brands"])


@router.post("", response_model=BrandCreateResponse)
def create_brand(req: BrandCreateRequest):
    """Create a new brand.

    Args:
        req: Brand creation request with name.

    Returns:
        BrandCreateResponse: Created brand with auto-generated ID.

    Raises:
        HTTPException: 500 if database insert fails.
    """
    sb = get_supabase()
    res = sb.table("brands").insert({"name": req.name}).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create brand")
    row = res.data[0]
    return BrandCreateResponse(id=row["id"], name=row["name"])


@router.post("/{brand_id}/manual")
async def create_manual(brand_id: str, body: dict):
    """Create a new brand manual (DNA guidelines).

    Orchestrates the full manual generation workflow:
    1. Generate manual structure with Groq LLM
    2. Validate and normalize data types
    3. Chunk manual for vector embeddings
    4. Store chunks with embeddings for RAG retrieval
    5. Persist manual metadata

    Heavy lifting delegated to services.brand_manual.create_brand_manual()
    which encapsulates prompt generation, LLM invocation, validation and
    persistence. This route remains responsible for raising HTTP errors if
    the service raises unexpected exceptions.

    Args:
        brand_id: Brand identifier.
        body: Manual generation parameters (brand context, guidelines, etc.).

    Returns:
        dict: Generated manual with structure validation results.

    Raises:
        HTTPException: 400 for validation errors, 500 for LLM/DB failures.
    """
    try:
        return await create_brand_manual(brand_id, body)
    except HTTPException:
        # propagate any HTTPExceptions raised by lower layers
        raise
    except Exception as exc:
        # unexpected failures are converted into 500s
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{brand_id}/manual")
def get_latest_manual(brand_id: str):
    """Get the most recent manual for a brand.

    Retrieves cached manual from repository layer.

    Args:
        brand_id: Brand identifier.

    Returns:
        dict: Manual data with all guidelines and structure.

    Raises:
        HTTPException: 404 if no manual exists for brand.
    """
    rec = manual_repo.get_latest_manual(brand_id)
    if not rec:
        raise HTTPException(status_code=404, detail="No manual found for brand")
    return rec


@router.get("")
def list_brands():
    """List all brands ordered by creation date (newest first).

    Returns:
        list: Brand records with id, name, created_at (max 50).
    """
    sb = get_supabase()
    res = (
        sb.table("brands")
        .select("id, name, created_at")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return res.data or []
