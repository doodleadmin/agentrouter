"""Helper functions for building PermissionContext objects (SEC-01)."""

from app.db.enums import ActorType
from app.security.permissions import PermissionAction, PermissionContext


def context_for_telegram_user(
    user_id: str | int,
    action: PermissionAction,
    *,
    task_id: str | None = None,
    project_id: str | None = None,
    agent_id: str | None = None,
    risk_level=None,
    source: str = "telegram",
    **kwargs,
) -> PermissionContext:
    """Create PermissionContext for a Telegram user action."""
    return PermissionContext(
        actor_type=ActorType.USER,
        actor_id=str(user_id),
        source=source,
        action=action,
        task_id=task_id,
        project_id=project_id,
        agent_id=agent_id,
        risk_level=risk_level,
    )


def context_for_system(
    action: PermissionAction,
    *,
    task_id: str | None = None,
    project_id: str | None = None,
    agent_id: str | None = None,
    **kwargs,
) -> PermissionContext:
    """Create PermissionContext for a system/internal action."""
    return PermissionContext(
        actor_type=ActorType.SYSTEM,
        source="system",
        action=action,
        task_id=task_id,
        project_id=project_id,
        agent_id=agent_id,
    )


def context_for_callback(
    user_id: str | int,
    action: PermissionAction,
    *,
    task_id: str | None = None,
    project_id: str | None = None,
    agent_id: str | None = None,
    risk_level=None,
    **kwargs,
) -> PermissionContext:
    """Create PermissionContext for a Telegram callback action."""
    return PermissionContext(
        actor_type=ActorType.USER,
        actor_id=str(user_id),
        source="telegram",
        action=action,
        task_id=task_id,
        project_id=project_id,
        agent_id=agent_id,
        risk_level=risk_level,
    )
