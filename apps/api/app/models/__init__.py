"""Register all SQLAlchemy models for metadata discovery."""

from app.models.agent import Agent
from app.models.approval import Approval
from app.models.memory_chunk import MemoryChunk
from app.models.memory_document import MemoryDocument
from app.models.project import Project
from app.models.security_audit import SecurityAuditEvent
from app.models.task import Task
from app.models.task_event import TaskEvent
from app.models.telegram_topic import TelegramTopic

__all__ = [
    "Project",
    "Agent",
    "TelegramTopic",
    "Task",
    "Approval",
    "TaskEvent",
    "SecurityAuditEvent",
    "MemoryDocument",
    "MemoryChunk",
]
