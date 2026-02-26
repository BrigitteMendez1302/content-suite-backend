from fastapi import APIRouter

from app.services.manual import get_manual

router = APIRouter(prefix="/manuals", tags=["manuals"])


@router.get("/{manual_id}")
def get_manual_endpoint(manual_id: str):
    """Retrieve a manual document by its ID."""
    return get_manual(manual_id)
