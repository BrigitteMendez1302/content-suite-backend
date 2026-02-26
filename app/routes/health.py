"""Health check endpoint for API availability monitoring."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    """Check API health status.

    Returns:
        dict: {"ok": True} if service is running and responding normally.

    Note:
        Useful for uptime monitoring, load balancers, and health probes.
        Returns immediately without database checks for speed.
    """
    return {"ok": True}