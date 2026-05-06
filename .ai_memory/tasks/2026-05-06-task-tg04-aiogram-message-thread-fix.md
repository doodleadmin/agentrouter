# Task Summary: TG-04 aiogram 3.15 message_thread_id compatibility fix

**Date:** 2026-05-06
**Agent:** studio-orchestrator (coordinated execution)
**Contour:** local only; no deploy/migrations/secrets/OpenCode

## Problem

After `/start` command in private chat, aiogram 3.15.0 raised:
```
TypeError: aiogram.methods.send_message.SendMessage() got multiple values for keyword argument 'message_thread_id'
```

**Root cause:** All handler files used `message.answer(text, message_thread_id=_thread_id(message))`. In aiogram 3.15, `message.answer()` automatically propagates `message_thread_id` from the incoming message context. Passing it explicitly caused a duplicate keyword argument error.

## Fix

Removed explicit `message_thread_id=_thread_id(message)` from all `message.answer()` calls across 10 handler files. Removed `_thread_id()` helper functions from all files. aiogram 3.15 handles thread routing automatically.

## Changed Files (17 total)

### Handlers (10 files):
- `apps/telegram-bot/app/handlers/start.py` — removed `_thread_id()` + explicit kwarg from 2 `message.answer()` calls
- `apps/telegram-bot/app/handlers/commands.py` — removed `_thread_id()` + explicit kwarg from 3 `message.answer()` calls
- `apps/telegram-bot/app/handlers/messages.py` — removed `_thread_id()` + explicit kwarg from 2 `message.answer()` calls
- `apps/telegram-bot/app/handlers/status_handler.py` — removed `_thread_id()` + explicit kwarg from 3 `message.answer()` calls
- `apps/telegram-bot/app/handlers/approve_handler.py` — removed `_thread_id()` + explicit kwarg from 7 `message.answer()` calls
- `apps/telegram-bot/app/handlers/reject_handler.py` — removed `_thread_id()` + explicit kwarg from 7 `message.answer()` calls
- `apps/telegram-bot/app/handlers/plan_handler.py` — removed `_thread_id()` + explicit kwarg from 3 `message.answer()` calls
- `apps/telegram-bot/app/handlers/topic_status.py` — removed `_thread_id()` + explicit kwarg from 3 `message.answer()` calls
- `apps/telegram-bot/app/handlers/bind_topic.py` — removed `_thread_id()` + explicit kwarg from 6 `message.answer()` calls
- `apps/telegram-bot/app/handlers/unbind_topic.py` — removed `_thread_id()` + explicit kwarg from 3 `message.answer()` calls

### Tests (7 files):
- `apps/telegram-bot/tests/test_messages.py` — updated FakeMessage.answer() signature, updated assertions
- `apps/telegram-bot/tests/test_commands_rendering.py` — updated FakeMessage.answer() signature, updated assertions
- `apps/telegram-bot/tests/test_status_handler.py` — updated FakeMessage.answer() signature
- `apps/telegram-bot/tests/test_approve_handler.py` — updated FakeMessage.answer() signature
- `apps/telegram-bot/tests/test_reject_handler.py` — updated FakeMessage.answer() signature
- `apps/telegram-bot/tests/test_plan_handler.py` — updated FakeMessage.answer() signature
- `apps/telegram-bot/tests/test_bind_unbind_topic_handlers.py` — updated FakeMessage.answer() signature, updated assertions

## Validation Results

- `python -m compileall app` ✅
- `ruff check app` ✅ — All checks passed!
- `pytest tests -v` ✅ — 64/64 passed in 3.10s
- `git check-ignore .env.local` ✅ — .env.local is gitignored
- No secrets/tokens/credentials in changes

## Security Verdict

- PASS: No tokens/secrets printed or logged
- PASS: .env.local not touched
- PASS: CALLBACK_SECRET not touched
- PASS: admin IDs not touched
- PASS: API code not changed
- PASS: OpenCode/runtime code not changed

## Key Insight

aiogram 3.15 changed behavior: `message.answer()` now automatically propagates `message_thread_id` from the incoming message. Explicit passing causes `TypeError: got multiple values for keyword argument`. The fix is to simply remove the explicit `message_thread_id` parameter from all `message.answer()` calls — aiogram handles it automatically for both private chats and forum topics.
