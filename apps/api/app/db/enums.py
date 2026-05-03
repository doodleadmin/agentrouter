"""Database-related enums shared by SQLAlchemy models."""

from enum import StrEnum


class TopicKind(StrEnum):
    AGENT = "agent"
    PROJECT = "project"
    GENERAL = "general"
    APPROVALS = "approvals"
    SYSTEM = "system"


class TaskStatus(StrEnum):
    CREATED = "created"
    ROUTED = "routed"
    PLANNING = "planning"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    RUNNING = "running"
    TESTS_RUNNING = "tests_running"
    PR_CREATED = "pr_created"
    DEPLOYING_STAGING = "deploying_staging"
    DEPLOYING_PRODUCTION = "deploying_production"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ActorType(StrEnum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
