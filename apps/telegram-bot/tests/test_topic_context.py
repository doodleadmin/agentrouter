from app.services.topic_context import resolve_topic_context


class FakeApiClient:
    def __init__(self, topics):
        self._topics = topics

    async def list_topics(self):
        return self._topics


async def test_resolve_topic_context_bound() -> None:
    client = FakeApiClient(
        [
            {
                "chat_id": 123,
                "message_thread_id": 456,
                "kind": "project",
                "project_id": "proj-1",
                "agent_id": None,
                "title": "Project: demo",
            }
        ]
    )

    ctx = await resolve_topic_context(123, 456, api_client=client)

    assert ctx.is_bound is True
    assert ctx.kind == "project"
    assert ctx.project_id == "proj-1"
    assert ctx.title == "Project: demo"


async def test_resolve_topic_context_unbound() -> None:
    client = FakeApiClient([])
    ctx = await resolve_topic_context(1, 2, api_client=client)
    assert ctx.is_bound is False
