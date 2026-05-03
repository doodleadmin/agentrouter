"""Resolve Telegram topic binding context using backend topic registry."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.api_client import ApiClient, get_api_client


@dataclass(slots=True)
class TopicContext:
    """Resolved Telegram topic context."""

    is_bound: bool
    kind: str | None = None
    project_id: str | None = None
    agent_id: str | None = None
    title: str | None = None


async def resolve_topic_context(
    chat_id: int,
    message_thread_id: int | None,
    api_client: ApiClient | None = None,
) -> TopicContext:
    """Find matching topic binding by chat_id + message_thread_id."""

    client = api_client or get_api_client()
    thread_id = message_thread_id or 0
    topics = await client.list_topics()

    for topic in topics:
        if int(topic.get("chat_id", -1)) == chat_id and int(topic.get("message_thread_id", -1)) == thread_id:
            return TopicContext(
                is_bound=True,
                kind=topic.get("kind"),
                project_id=topic.get("project_id"),
                agent_id=topic.get("agent_id"),
                title=topic.get("title"),
            )

    return TopicContext(is_bound=False)
