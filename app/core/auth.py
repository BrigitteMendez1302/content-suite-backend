"""Authentication and authorization using Supabase Auth and role-based access control."""
from fastapi import Depends, HTTPException, Header
from app.db.supabase_client import get_supabase


def _bearer_token(authorization: str | None) -> str:
    """Extract bearer token from Authorization header.

    Args:
        authorization: Contents of Authorization header (expected format:
                      "Bearer <token>").

    Returns:
        str: The token string (without "Bearer" prefix).

    Raises:
        HTTPException: 401 if header missing or malformed.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return parts[1]

async def get_current_user(authorization: str | None = Header(default=None)):
    """Verify JWT token and return user info from Supabase Auth.

    Validates the token with Supabase and extracts user id and email.

    Args:
        authorization: HTTP Authorization header value.

    Returns:
        dict: {"id": user_id, "email": user_email}

    Raises:
        HTTPException: 401 if token is invalid or cannot be verified.
    """
    token = _bearer_token(authorization)
    sb = get_supabase()
    try:
        user_resp = sb.auth.get_user(token)
        user = user_resp.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"id": user.id, "email": user.email}

async def get_current_profile(user=Depends(get_current_user)):
    """Get or create user profile with role.

    Fetches user profile from profiles table. If profile doesn't exist,
    creates one with default role "creator".

    Args:
        user: User dict from get_current_user (injected via Depends).

    Returns:
        dict: {"id": user_id, "email": user_email, "role": role_string}

    Note:
        If the user profile doesn't exist, it's auto-created with role="creator".
    """
    sb = get_supabase()
    pres = sb.table("profiles").select("id,email,role").eq("id", user["id"]).limit(1).execute()
    if not pres.data:
        sb.table("profiles").insert({"id": user["id"], "email": user["email"], "role": "creator"}).execute()
        role = "creator"
    else:
        role = pres.data[0]["role"]
    return {**user, "role": role}

def require_roles(*roles: str):
    """Dependency factory for role-based access control.

    Returns a dependency function that checks if the current user's role
    is in the allowed list.

    Args:
        *roles: One or more allowed role strings (e.g., "creator",
               "approver_a", "approver_b").

    Returns:
        Callable: A dependency function that raises 403 if role not allowed,
                 otherwise returns the profile dict.

    Raises:
        HTTPException: 403 Forbidden if user's role is not in allowed list.

    Example:
        >>> @router.post("/approve")
        >>> async def approve(item_id: str,
        >>>                   profile=Depends(require_roles("approver_a", "approver_b"))):
        >>>     # Only users with approver_a or approver_b role can access
        >>>     return {"approved": True}
    """
    async def _dep(profile=Depends(get_current_profile)):
        if profile["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return profile
    return _dep