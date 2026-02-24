from fastapi import APIRouter, Depends
from app.core.auth import get_current_profile

router = APIRouter(tags=["auth"])

@router.get("/me")
async def me(profile=Depends(get_current_profile)):
    return {"id": profile["id"], "email": profile["email"], "role": profile["role"]}