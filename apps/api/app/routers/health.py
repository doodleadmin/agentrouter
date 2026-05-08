"""
Health check endpoint.

GET /health — returns system status with dependency checks.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.config import settings
from app.db.session import AsyncSessionLocal

# Module-level import so tests can patch ``app.routers.health.aioredis``.
try:
    import redis.asyncio as aioredis
except ImportError:  # pragma: no cover — redis is a declared dependency
    aioredis = None  # type: ignore[assignment]

router = APIRouter(tags=["health"])


async def _check_database() -> str:
    """Return 'ok' if PostgreSQL is reachable, else 'error'."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


async def _check_redis() -> str:
    """Return 'ok' if Redis is reachable, else 'error'."""
    if aioredis is None:
        return "unavailable"
    try:
        async with aioredis.from_url(settings.REDIS_URL) as r:
            await r.ping()
        return "ok"
    except Exception:
        return "error"


@router.get("/health")
async def health_check(response: Response) -> dict:
    """
    Health check endpoint.

    Checks connectivity to PostgreSQL and Redis.
    Returns HTTP 200 always (backward compatible).
    ``status`` is ``"ok"`` when all checks pass, ``"degraded"`` otherwise.
    """
    checks = {
        "api": "ok",
        "database": await _check_database(),
        "redis": await _check_redis(),
    }

    all_ok = all(v == "ok" for v in checks.values())

    return {
        "status": "ok" if all_ok else "degraded",
        "service": "agent-mission-control-api",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
