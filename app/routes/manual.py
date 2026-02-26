"""Brand manual retrieval endpoints.

Provides read-only access to stored brand manual documents.
Manuals define comprehensive brand guidelines used throughout the system.
"""
from fastapi import APIRouter

from app.services.manual import get_manual

router = APIRouter(prefix="/manuals", tags=["manuals"])


@router.get("/{manual_id}")
def get_manual_endpoint(manual_id: str):
    """Retrieve a brand manual by its ID.

    Args:
        manual_id: Manual identifier (UUID format).

    Returns:
        dict: Complete manual with all guidelines and structure.

    Raises:
        HTTPException: 404 if manual not found.
    """
    return get_manual(manual_id)
