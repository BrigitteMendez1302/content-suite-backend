from typing import Any, Dict, Optional

from app.repositories import brand_manual as manual_repo
from fastapi import HTTPException


def get_rules(brand_id: str) -> Dict[str, Any]:
    """Return the visual rules for a brand.

    Always returns a dict with keys colors, logo_rules, typography, image_style,
    notes.  This mirrors the behaviour of the original route.
    """
    return manual_repo.get_visual_rules(brand_id)


def upsert_rules(brand_id: str, rules: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update the visual rules for a brand.

    Raises HTTPException(500) if the database operation fails.
    """
    res = manual_repo.upsert_visual_rules(brand_id, rules)
    if not res:
        raise HTTPException(status_code=500, detail="Failed to save visual rules")
    return res
