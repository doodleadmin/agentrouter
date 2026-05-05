"""
Health check endpoint.

GET /health — returns system status.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Response

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(response: Response) -> dict:
    """
    Health check endpoint.

    Returns:
        dict: System status with timestamp.
    """
    return {
        "status": "ok",
        "service": "agent-mission-control-api",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
