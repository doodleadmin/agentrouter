"""Async client for Orchestrator API endpoints used by bot."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class ApiClient:
    """Thin async client used by bot handlers."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None) -> None:
        self._client = httpx.AsyncClient(
            base_url=(base_url or settings.API_BASE_URL).rstrip("/"),
            timeout=timeout or settings.API_TIMEOUT_SECONDS,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def list_projects(self) -> list[dict[str, Any]]:
        response = await self._client.get("/projects", params={"active_only": True})
        response.raise_for_status()
        return response.json()

    async def list_agents(self) -> list[dict[str, Any]]:
        response = await self._client.get("/agents", params={"active_only": True})
        response.raise_for_status()
        return response.json()

    async def list_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        response = await self._client.get("/tasks", params={"limit": limit, "offset": 0})
        response.raise_for_status()
        return response.json()

    async def list_topics(self, active_only: bool | None = True) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if active_only is not None:
            params["active_only"] = active_only
        response = await self._client.get("/telegram/topics", params=params)
        response.raise_for_status()
        return response.json()

    async def find_project_by_slug(self, slug: str) -> dict[str, Any] | None:
        projects = await self.list_projects()
        for project in projects:
            if project.get("slug") == slug:
                return project
        return None

    async def find_agent_by_slug(self, slug: str) -> dict[str, Any] | None:
        agents = await self.list_agents()
        for agent in agents:
            if agent.get("slug") == slug:
                return agent
        return None

    async def find_topic_binding(self, chat_id: int, message_thread_id: int | None) -> dict[str, Any] | None:
        target_thread = message_thread_id or 0
        topics = await self.list_topics(active_only=None)
        for topic in topics:
            if int(topic.get("chat_id", -1)) == chat_id and int(topic.get("message_thread_id", -1)) == target_thread:
                return topic
        return None

    async def create_topic_binding(
        self,
        chat_id: int,
        message_thread_id: int,
        title: str,
        project_id: str,
        agent_id: str,
    ) -> dict[str, Any]:
        payload = {
            "chat_id": chat_id,
            "message_thread_id": message_thread_id,
            "title": title,
            "kind": "project",
            "project_id": project_id,
            "agent_id": agent_id,
            "is_active": True,
        }
        response = await self._client.post("/telegram/topics", json=payload)
        response.raise_for_status()
        return response.json()

    async def update_topic_binding(
        self,
        topic_id: str,
        title: str,
        project_id: str,
        agent_id: str,
        is_active: bool = True,
    ) -> dict[str, Any]:
        payload = {
            "title": title,
            "kind": "project",
            "project_id": project_id,
            "agent_id": agent_id,
            "is_active": is_active,
        }
        response = await self._client.patch(f"/telegram/topics/{topic_id}", json=payload)
        response.raise_for_status()
        return response.json()

    async def deactivate_topic_binding(self, topic_id: str) -> dict[str, Any]:
        response = await self._client.delete(f"/telegram/topics/{topic_id}")
        response.raise_for_status()
        return response.json()

    async def create_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post("/tasks", json=payload)
        response.raise_for_status()
        return response.json()

    async def trigger_plan(self, task_id: str) -> dict[str, Any]:
        """Trigger plan pipeline for a task via backend API."""
        response = await self._client.post(f"/tasks/{task_id}/trigger-plan")
        response.raise_for_status()
        return response.json()

    # ── TG-03: Approval + task UX methods ──────────────────────────────

    async def get_task(self, task_id: str) -> dict[str, Any]:
        """Get a single task by id."""
        response = await self._client.get(f"/tasks/{task_id}")
        response.raise_for_status()
        return response.json()

    async def get_task_plan(self, task_id: str) -> dict[str, Any]:
        """Get plan text for a task."""
        response = await self._client.get(f"/tasks/{task_id}/plan")
        response.raise_for_status()
        return response.json()

    async def list_task_events(self, task_id: str) -> list[dict[str, Any]]:
        """List audit events for a task."""
        response = await self._client.get(f"/events/tasks/{task_id}/events")
        response.raise_for_status()
        return response.json()

    async def list_approvals_by_task(self, task_id: str) -> list[dict[str, Any]]:
        """List approvals for a task."""
        response = await self._client.get(f"/approvals/tasks/{task_id}/approvals")
        response.raise_for_status()
        return response.json()

    async def approve_approval(
        self, approval_id: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Approve an approval request."""
        response = await self._client.post(
            f"/approvals/{approval_id}/approve",
            json=body or {},
        )
        response.raise_for_status()
        return response.json()

    async def reject_approval(
        self, approval_id: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Reject an approval request."""
        response = await self._client.post(
            f"/approvals/{approval_id}/reject",
            json=body or {},
        )
        response.raise_for_status()
        return response.json()

    async def callback_answer(self, task_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Validate a callback action and get task+approval state snapshot."""
        response = await self._client.post(
            f"/tasks/{task_id}/callback-answer",
            json=body,
        )
        response.raise_for_status()
        return response.json()

    async def find_task_by_external_id(self, external_id: str) -> dict[str, Any] | None:
        """Find a task by its external_id by scanning recent tasks."""
        tasks = await self.list_tasks(limit=100)
        for task in tasks:
            if task.get("external_id") == external_id:
                return task
        return None


_api_client: ApiClient | None = None


def get_api_client() -> ApiClient:
    """Singleton-like accessor for bot process-level API client."""

    global _api_client
    if _api_client is None:
        _api_client = ApiClient()
    return _api_client


async def close_api_client() -> None:
    """Close process-level client gracefully."""

    global _api_client
    if _api_client is not None:
        await _api_client.close()
        _api_client = None
