"""OpenCode client abstraction and BE-03 plan-only stub implementation."""

from __future__ import annotations

from typing import Protocol

from app.integrations.opencode.schemas import RuntimePlanContext, RuntimePlanResult


class OpenCodeClientProtocol(Protocol):
    """Runtime adapter contract to enable future real OpenCode integration."""

    async def generate_plan(self, context: RuntimePlanContext) -> RuntimePlanResult:
        """Generate execution plan from task context without executing code."""


class StubOpenCodeClient:
    """Deterministic fake runtime adapter used for BE-03 plan-only mode."""

    async def generate_plan(self, context: RuntimePlanContext) -> RuntimePlanResult:
        plan = (
            "## Plan\n"
            f"1. Analyze task for project `{context.project_slug}` and agent `{context.agent_slug}`.\n"
            "2. Identify likely files/modules impacted by requested change.\n"
            "3. Propose validation steps and rollback considerations.\n\n"
            "## Task Context\n"
            f"- Agent role: {context.agent_role}\n"
            f"- Raw task: {context.raw_text}\n"
            f"- Normalized task: {context.normalized_text}\n"
            f"- Repo path: {context.repo_path}\n"
            f"- Memory path: {context.memory_path}\n\n"
            "## Safety\n"
            "- Mode: plan-only\n"
            "- No code execution\n"
            "- No file modifications\n"
        )
        return RuntimePlanResult(plan_text=plan)
