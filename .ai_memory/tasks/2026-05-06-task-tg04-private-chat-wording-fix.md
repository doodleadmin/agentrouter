---
date: 2026-05-06
task_id: tg04-private-chat-wording-fix
status: completed
agent: studio-orchestrator
---

# TG-04: Private Chat Wording Fix

## Problem
In private chat, the unbound-topic message said "Этот topic пока не привязан..." — the word "topic" is confusing in a 1:1 private chat context.

## Solution
Check `message.chat.type`: use "чат" for `private`, "topic" for group/forum.

## Files Changed
| File | Change |
|------|--------|
| `apps/telegram-bot/app/handlers/messages.py` | Added `is_private = message.chat.type == "private"`, dynamic `label` ("чат" / "topic") |
| `apps/telegram-bot/tests/test_messages.py` | Added `chat_type` param to `FakeMessage`, added `test_text_message_unbound_private_chat` |

## Validation
- `python -m compileall app` ✅
- `ruff check app` ✅
- `pytest tests -v` ✅ (65/65 passed, +1 new test)

## Security
- No secrets touched
- No .env files modified
- No live Telegram bot started
