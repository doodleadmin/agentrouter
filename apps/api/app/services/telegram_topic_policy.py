"""Topic role policy — backend-level validation for topic kinds and constraints.

Formalizes the allowed topic roles and enforces semantic constraints
at the service/policy layer (schema-level validation is in
``app.schemas.telegram_topic`` via Literal type).

Allowed kinds:
    general      — default chat, system messages, coordination
    agent        — bound to a single agent
    approvals    — approval flow notifications
    system_logs  — infrastructure / deploy / error logs
    task         — per-task conversation thread

Policy rules (enforced here):
    1. ``agent`` kind REQUIRES ``agent_id`` to be set.
    2. ``task`` kind REQUIRES ``project_id`` to be set.
    3. ``general``, ``approvals``, ``system_logs`` kinds SHOULD NOT have
       ``agent_id`` set (warning-level, not enforced as error for flexibility).
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


# Canonical set of valid topic kinds — single source of truth.
VALID_TOPIC_KINDS: frozenset[str] = frozenset({
    "general",
    "agent",
    "approvals",
    "system_logs",
    "task",
})


@dataclass(frozen=True)
class TopicPolicyViolation:
    """A single policy rule violation."""

    field: str
    rule: str
    message: str


def validate_topic_policy(
    *,
    kind: str,
    agent_id: UUID | None = None,
    project_id: UUID | None = None,
) -> list[TopicPolicyViolation]:
    """Validate topic binding against role policy rules.

    Returns a (possibly empty) list of violations.
    Empty list = policy passes.
    """
    violations: list[TopicPolicyViolation] = []

    if kind not in VALID_TOPIC_KINDS:
        violations.append(TopicPolicyViolation(
            field="kind",
            rule="valid_kind",
            message=f"Invalid topic kind '{kind}'. Allowed: {sorted(VALID_TOPIC_KINDS)}",
        ))
        return violations  # short-circuit: other rules assume valid kind

    # Rule 1: agent kind requires agent_id
    if kind == "agent" and agent_id is None:
        violations.append(TopicPolicyViolation(
            field="agent_id",
            rule="agent_kind_requires_agent_id",
            message="Topic kind 'agent' requires agent_id to be set",
        ))

    # Rule 2: task kind requires project_id
    if kind == "task" and project_id is None:
        violations.append(TopicPolicyViolation(
            field="project_id",
            rule="task_kind_requires_project_id",
            message="Topic kind 'task' requires project_id to be set",
        ))

    return violations
