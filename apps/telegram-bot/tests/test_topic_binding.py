from app.services.topic_binding import parse_bind_topic_args


def test_parse_bind_topic_args_ok() -> None:
    parsed = parse_bind_topic_args("/bind_topic project=academy-bot agent=backend")
    assert parsed is not None
    assert parsed.project_slug == "academy-bot"
    assert parsed.agent_slug == "backend"


def test_parse_bind_topic_args_missing() -> None:
    parsed = parse_bind_topic_args("/bind_topic project=academy-bot")
    assert parsed is None
