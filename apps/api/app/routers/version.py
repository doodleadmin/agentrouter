"""
Version endpoint.

GET /version — returns application metadata including version, build info,
and runtime environment.
"""

import sys

from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["version"])


@router.get("/version")
async def version() -> dict:
    """
    Return full application version information.

    Fields:
    - **version** — semantic version string (from `APP_VERSION` env / default)
    - **name** — service name (from `APP_NAME` env / default)
    - **commit_sha** — git commit SHA injected at build time
    - **build_time** — ISO-8601 timestamp of the build
    - **python_version** — Python runtime version
    - **debug** — whether DEBUG mode is enabled

    Returns:
        dict: Version and build metadata.
    """
    return {
        "version": settings.APP_VERSION,
        "name": settings.APP_NAME,
        "commit_sha": settings.COMMIT_SHA,
        "build_time": settings.BUILD_TIME,
        "python_version": sys.version.split()[0],
        "debug": settings.DEBUG,
    }
