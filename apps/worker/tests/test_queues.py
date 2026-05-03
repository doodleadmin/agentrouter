"""Tests for queue constants."""

from app.queues import ALL_QUEUES, DEPLOY_PRODUCTION, TELEGRAM_INBOUND


def test_all_queues_count() -> None:
    assert len(ALL_QUEUES) == 7


def test_queue_names() -> None:
    expected = {
        "telegram_inbound",
        "agent_plan",
        "agent_execute",
        "memory_index",
        "deploy_staging",
        "deploy_production",
        "notifications",
    }
    assert set(ALL_QUEUES) == expected


def test_specific_queues() -> None:
    assert TELEGRAM_INBOUND == "telegram_inbound"
    assert DEPLOY_PRODUCTION == "deploy_production"
