"""Named queues for Celery task routing.

Each queue corresponds to a domain of background work.
Queues are explicitly declared so that workers only consume
from the queues they are assigned to.
"""

TELEGRAM_INBOUND = "telegram_inbound"
AGENT_PLAN = "agent_plan"
AGENT_EXECUTE = "agent_execute"
MEMORY_INDEX = "memory_index"
DEPLOY_STAGING = "deploy_staging"
DEPLOY_PRODUCTION = "deploy_production"
NOTIFICATIONS = "notifications"

ALL_QUEUES: list[str] = [
    TELEGRAM_INBOUND,
    AGENT_PLAN,
    AGENT_EXECUTE,
    MEMORY_INDEX,
    DEPLOY_STAGING,
    DEPLOY_PRODUCTION,
    NOTIFICATIONS,
]
