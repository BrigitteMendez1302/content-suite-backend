"""Brand visual rules management endpoints.

CRUD operations for visual guidelines (colors, typography, logo rules, etc.).
Used during content generation and image audits.
All business logic delegated to service layer.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.core.auth import require_roles
from app.services.visual_rules import get_rules, upsert_rules

router = APIRouter(prefix="/brands", tags=["visual-rules"])


class VisualRulesBody(BaseModel):
    """Visual guidelines for a brand.

    Attributes:
        colors: Brand color palette descriptions.
        logo_rules: Guidelines for logo usage and placement.
        typography: Font families and hierarchy rules.
        image_style: Photography and image style guidelines.
        notes: Additional visual guidance notes.
    """
    colors: list[str] = []
    logo_rules: list[str] = []
    typography: list[str] = []
    image_style: list[str] = []
    notes: Optional[str] = None


@router.get("/{brand_id}/visual-rules")
async def get_visual_rules(brand_id: str, profile=Depends(require_roles("creator","approver_a","approver_b"))):
    """Retrieve visual guidelines for a brand.

    Requires one of: creator, approver_a, approver_b role.

    Args:
        brand_id: Brand identifier.
        profile: Current user profile (role validated via Depends).

    Returns:
        dict: Visual rules with metadata (created_at, updated_at).

    Raises:
        HTTPException: 403 if insufficient role, 404 if not found.
    """
    return get_rules(brand_id)


@router.put("/{brand_id}/visual-rules")
async def upsert_visual_rules(brand_id: str, body: VisualRulesBody):
    """Create or update visual guidelines for a brand.

    Stores rules for reference during content generation and image audits.

    Args:
        brand_id: Brand identifier.
        body: Visual guidelines with colors, fonts, logo rules, etc.

    Returns:
        dict: Stored visual rules with metadata.

    Raises:
        HTTPException: 400 for invalid brand, 500 for DB failures.
    """
    payload = body.model_dump()
    return upsert_rules(brand_id, payload)
