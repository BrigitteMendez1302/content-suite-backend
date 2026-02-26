"""User profile endpoint."""
from fastapi import APIRouter, Depends
from app.core.auth import get_current_profile

router = APIRouter(tags=["auth"])


@router.get("/me")
async def me(profile=Depends(get_current_profile)):
    """Get current authenticated user profile.

    Requires valid JWT token in Authorization header.

    Args:
        profile: Current user profile (injected via Depends).

    Returns:
        dict: {"id": user_id, "email": user_email, "role": role}

    Raises:
        HTTPException: 401 if not authenticated or token invalid.
    """
    return {"id": profile["id"], "email": profile["email"], "role": profile["role"]}