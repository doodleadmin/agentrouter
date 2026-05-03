"""Memory index task — triggers backend memory reindex endpoint."""

from __future__ import annotations

import logging

import httpx

from app.celery_app import celery_app
from app.config import settings
from app.queues import MEMORY_INDEX

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.memory_index",
    queue=MEMORY_INDEX,
    max_retries=settings.TASK_MAX_RETRIES,
    autoretry_for=(Exception,),
    retry_backoff=settings.TASK_RETRY_BACKOFF,
    retry_backoff_max=settings.TASK_RETRY_BACKOFF_MAX,
    retry_jitter=settings.TASK_RETRY_JITTER,
)
def index_memory(scope: str = "all", project_slug: str | None = None) -> dict:
    """Trigger backend reindexing of `.ai_memory` markdown documents.

    Args:
        scope: Indexing scope — "all", "global", "project", "tasks", "decisions", "agents".
        project_slug: Optional project slug for scoped indexing.

    Returns:
        Reindex result dict from backend or error payload.
    """
    api = settings.API_BASE_URL.rstrip("/")
    url = f"{api}/memory/reindex"

    logger.info("memory_index: scope=%s project=%s", scope, project_slug)

    payload: dict[str, str] = {"scope": scope}
    if project_slug:
        payload["project_slug"] = project_slug

    try:
        with httpx.Client(timeout=settings.API_TIMEOUT_SECONDS) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        return {
            "status": "ok",
            "scope": data.get("scope", scope),
            "project_slug": data.get("project_slug", project_slug),
            "scanned_files": data.get("scanned_files", 0),
            "indexed_documents": data.get("indexed_documents", 0),
            "skipped_documents": data.get("skipped_documents", 0),
            "total_chunks": data.get("total_chunks", 0),
        }
    except httpx.HTTPError as exc:
        logger.warning("memory_index: HTTP error scope=%s project=%s error=%s", scope, project_slug, exc)
        return {
            "status": "error",
            "scope": scope,
            "project_slug": project_slug,
            "error": str(exc),
        }
