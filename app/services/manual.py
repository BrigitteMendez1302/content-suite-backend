from typing import Any, Dict
from fastapi import HTTPException

from app.repositories import manual as manual_repo


def get_manual(manual_id: str) -> Dict[str, Any]:
    """Service helper returning a manual by id.

    Raises ``HTTPException(404)`` if the manual isn't found so that the caller
    (route) can simply return the result.
    """
    rec = manual_repo.get_manual_by_id(manual_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Manual not found")
    return rec
