"""Deploy tasks — staging and production stubs.

deploy_staging: stub that simulates a staging deploy.
deploy_production: always returns blocked/requires_approval.

For WRK-01 both are stubs. Real deploy requires DOP-04.
"""

import logging

from app.celery_app import celery_app
from app.config import settings
from app.queues import DEPLOY_PRODUCTION, DEPLOY_STAGING

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.deploy_staging",
    queue=DEPLOY_STAGING,
    max_retries=settings.TASK_MAX_RETRIES,
    autoretry_for=(Exception,),
    retry_backoff=settings.TASK_RETRY_BACKOFF,
    retry_backoff_max=settings.TASK_RETRY_BACKOFF_MAX,
    retry_jitter=settings.TASK_RETRY_JITTER,
)
def deploy_staging(project_slug: str, branch: str) -> dict:
    """Deploy to staging (stub).

    Args:
        project_slug: Project to deploy.
        branch: Git branch to deploy.

    Returns:
        Stub result dict.
    """
    logger.info("deploy_staging: project=%s branch=%s — STUB", project_slug, branch)

    return {
        "status": "stub",
        "project_slug": project_slug,
        "branch": branch,
        "environment": "staging",
        "message": (
            "deploy_staging is a stub for WRK-01. "
            "Real staging deploy requires DOP-02 + DOP-04."
        ),
    }


@celery_app.task(
    name="tasks.deploy_production",
    queue=DEPLOY_PRODUCTION,
    max_retries=0,  # Never retry production deploy automatically
)
def deploy_production(project_slug: str, branch: str) -> dict:
    """Deploy to production — always blocked.

    Production deploy requires explicit approval (SEC-01, DOP-04).
    This task will NEVER execute real deploy logic.

    Args:
        project_slug: Project to deploy.
        branch: Git branch to deploy.

    Returns:
        Blocked result dict.
    """
    logger.warning(
        "deploy_production: BLOCKED — project=%s branch=%s",
        project_slug,
        branch,
    )

    return {
        "status": "blocked",
        "project_slug": project_slug,
        "branch": branch,
        "environment": "production",
        "message": (
            "Production deploy requires explicit approval. "
            "This task is blocked by policy (SEC-01, DOP-04)."
        ),
    }
