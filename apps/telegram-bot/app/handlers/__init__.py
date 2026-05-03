"""Handler routers aggregation."""

from app.handlers.bind_topic import router as bind_topic_router
from app.handlers.commands import router as commands_router
from app.handlers.messages import router as messages_router
from app.handlers.start import router as start_router
from app.handlers.topic_status import router as topic_status_router
from app.handlers.unbind_topic import router as unbind_topic_router

__all__ = [
    "start_router",
    "commands_router",
    "bind_topic_router",
    "unbind_topic_router",
    "topic_status_router",
    "messages_router",
]
