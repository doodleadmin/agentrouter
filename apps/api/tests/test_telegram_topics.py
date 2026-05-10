"""Tests for telegram topic schemas and router structure."""

import uuid

import pytest
from pydantic import ValidationError

from app.routers.telegram_topics import router
from app.schemas.telegram_topic import TelegramTopicCreate, TelegramTopicUpdate


class TestTelegramTopicCreateSchema:
    def test_valid_agent_binding(self):
        agent_id = uuid.uuid4()
        data = TelegramTopicCreate(
            chat_id=123456789,
            message_thread_id=42,
            title="Agent: Backend",
            kind="agent",
            agent_id=agent_id,
        )
        assert data.kind == "agent"
        assert data.agent_id == agent_id
        assert data.project_id is None
        assert data.is_active is True

    def test_rejects_negative_chat_id(self):
        with pytest.raises(ValidationError):
            TelegramTopicCreate(
                chat_id=-1,
                message_thread_id=1,
                title="Bad",
                kind="general",
            )

    def test_rejects_unsupported_kind(self):
        with pytest.raises(ValidationError):
            TelegramTopicCreate(
                chat_id=123,
                message_thread_id=1,
                title="Bad kind",
                kind="project",
            )

    def test_accepts_allowed_kinds(self):
        for kind in ["general", "agent", "approvals", "system_logs", "task"]:
            data = TelegramTopicCreate(
                chat_id=123,
                message_thread_id=1,
                title=f"Topic {kind}",
                kind=kind,
            )
            assert data.kind == kind


class TestTelegramTopicUpdateSchema:
    def test_deactivate(self):
        data = TelegramTopicUpdate(is_active=False)
        assert data.is_active is False
        assert data.title is None


class TestRouterStructure:
    def test_prefix(self):
        assert router.prefix == "/telegram/topics"

    def test_routes_exist(self):
        paths = {r.path for r in router.routes}
        assert "/telegram/topics" in paths
        assert "/telegram/topics/{topic_id}" in paths
