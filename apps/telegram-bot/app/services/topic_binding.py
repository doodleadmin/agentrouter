"""Topic binding argument parsing and helper formatting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BindTopicArgs:
    project_slug: str
    agent_slug: str


def parse_bind_topic_args(text: str) -> BindTopicArgs | None:
    """Parse `/bind_topic project=<slug> agent=<slug>` command payload."""

    parts = text.strip().split()
    if not parts:
        return None

    # parts[0] is command itself
    payload = parts[1:]
    kv: dict[str, str] = {}
    for item in payload:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        kv[key.strip().lower()] = value.strip()

    project_slug = kv.get("project")
    agent_slug = kv.get("agent")
    if not project_slug or not agent_slug:
        return None
    return BindTopicArgs(project_slug=project_slug, agent_slug=agent_slug)
