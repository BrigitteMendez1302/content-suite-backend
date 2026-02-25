from fastapi import Depends, HTTPException, Header
from app.db.supabase_client import get_supabase

def _bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return parts[1]

async def get_current_user(authorization: str | None = Header(default=None)):
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
    sb = get_supabase()
    pres = sb.table("profiles").select("id,email,role").eq("id", user["id"]).limit(1).execute()
    if not pres.data:
        sb.table("profiles").insert({"id": user["id"], "email": user["email"], "role": "creator"}).execute()
        role = "creator"
    else:
        role = pres.data[0]["role"]
    return {**user, "role": role}

def require_roles(*roles: str):
    async def _dep(profile=Depends(get_current_profile)):
        if profile["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return profile
    return _dep