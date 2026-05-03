"""Routers package — exports for main app registration."""

from app.routers.agents import router as agents_router
from app.routers.approvals import router as approvals_router
from app.routers.health import router as health_router
from app.routers.memory import router as memory_router
from app.routers.projects import router as projects_router
from app.routers.runtime import router as runtime_router
from app.routers.task_events import router as task_events_router
from app.routers.tasks import router as tasks_router
from app.routers.telegram_topics import router as telegram_topics_router

__all__ = [
    "health_router",
    "projects_router",
    "agents_router",
    "telegram_topics_router",
    "tasks_router",
    "approvals_router",
    "task_events_router",
    "runtime_router",
    "memory_router",
]
