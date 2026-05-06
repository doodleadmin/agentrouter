---
date: 2026-05-06
task_id: tg04-private-chat-binding-support
status: completed
agent: studio-orchestrator
---

# TG-04: Private Chat Binding Support

## Problem
`/bind_topic`, `/unbind_topic`, `/topic_status` all rejected private chats with "работает только внутри forum topic" because they checked `message.message_thread_id is None`.

## Solution
Private chats use `message_thread_id=0` as sentinel (DB column is NOT NULL BigInteger). The lookup logic in `topic_context.py` and `api_client.py` already handled `None → 0`.

## How Private Binding Works
- Private chat: `chat.type == "private"`, `message_thread_id = 0`
- Forum topic: `chat.type == "supergroup"`, `message_thread_id = actual topic id`
- DB unique constraint `(chat_id, message_thread_id)` handles both correctly

## Files Changed
| File | Change |
|------|--------|
| `bind_topic.py` | Removed forum-only guard; uses `thread_id=0` for private; "чат" vs "topic" label |
| `unbind_topic.py` | Removed forum-only guard; uses `thread_id=0` for private; "Чат" vs "Topic" label |
| `topic_status.py` | Removed forum-only guard; uses `thread_id=0` for private; added `html_escape` for IDs |
| `test_bind_unbind_topic_handlers.py` | Added `chat_type` to `FakeMessage`; replaced `test_bind_topic_forum_only` with `test_bind_topic_private_chat`; added `test_unbind_topic_private_chat`, `test_topic_status_private_chat_unbound` |

## Validation
- `python -m compileall app` ✅
- `ruff check app` ✅
- `pytest tests -v` ✅ (67/67 passed, +3 new tests, -1 removed)

## Security
- No secrets touched
- No .env modified
- No migrations needed (message_thread_id=0 fits existing NOT NULL BigInteger)
- Bot message loop guard unchanged
- HTML escaping applied to dynamic values in topic_status
