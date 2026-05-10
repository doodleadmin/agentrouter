"""Tests for topic role policy validation."""

import uuid

import pytest

from app.services.telegram_topic_policy import (
    VALID_TOPIC_KINDS,
    TopicPolicyViolation,
    validate_topic_policy,
)


class TestValidTopicKinds:
    def test_canonical_set(self):
        assert VALID_TOPIC_KINDS == frozenset({
            "general", "agent", "approvals", "system_logs", "task"
        })


class TestValidateTopicPolicy:
    def test_general_kind_passes_without_bindings(self):
        violations = validate_topic_policy(kind="general")
        assert violations == []

    def test_approvals_kind_passes_without_bindings(self):
        violations = validate_topic_policy(kind="approvals")
        assert violations == []

    def test_system_logs_kind_passes_without_bindings(self):
        violations = validate_topic_policy(kind="system_logs")
        assert violations == []

    def test_agent_kind_with_agent_id_passes(self):
        aid = uuid.uuid4()
        violations = validate_topic_policy(kind="agent", agent_id=aid)
        assert violations == []

    def test_agent_kind_without_agent_id_violates(self):
        violations = validate_topic_policy(kind="agent", agent_id=None)
        assert len(violations) == 1
        assert violations[0].field == "agent_id"
        assert violations[0].rule == "agent_kind_requires_agent_id"

    def test_task_kind_with_project_id_passes(self):
        pid = uuid.uuid4()
        violations = validate_topic_policy(kind="task", project_id=pid)
        assert violations == []

    def test_task_kind_without_project_id_violates(self):
        violations = validate_topic_policy(kind="task", project_id=None)
        assert len(violations) == 1
        assert violations[0].field == "project_id"
        assert violations[0].rule == "task_kind_requires_project_id"

    def test_invalid_kind_returns_violation(self):
        violations = validate_topic_policy(kind="project")
        assert len(violations) == 1
        assert violations[0].field == "kind"
        assert violations[0].rule == "valid_kind"
        assert "project" in violations[0].message

    def test_invalid_kind_short_circuits(self):
        """When kind is invalid, no other rules are checked."""
        violations = validate_topic_policy(kind="bogus", agent_id=None, project_id=None)
        assert len(violations) == 1  # only kind violation

    def test_agent_kind_with_both_bindings_passes(self):
        aid = uuid.uuid4()
        pid = uuid.uuid4()
        violations = validate_topic_policy(kind="agent", agent_id=aid, project_id=pid)
        assert violations == []

    def test_task_kind_with_both_bindings_passes(self):
        aid = uuid.uuid4()
        pid = uuid.uuid4()
        violations = validate_topic_policy(kind="task", agent_id=aid, project_id=pid)
        assert violations == []


class TestTopicPolicyViolation:
    def test_is_frozen(self):
        v = TopicPolicyViolation(field="k", rule="r", message="m")
        with pytest.raises(AttributeError):
            v.field = "x"  # type: ignore[misc]

    def test_fields(self):
        v = TopicPolicyViolation(field="f", rule="r", message="msg")
        assert v.field == "f"
        assert v.rule == "r"
        assert v.message == "msg"
