# TG-05 Phase 1: Live Telegram Notifications + Admin Approval Gate

**Date:** 2026-05-06
**Status:** COMPLETE
**Risk:** medium (admin gate security, process-scoped secrets)

---

## Objective

1. Give worker access to TELEGRAM_BOT_TOKEN via .env.local process-scoped sourcing.
2. Add fail-closed admin gate to /approve and /reject handlers.
3. Add unit tests for all changes.
4. No live Telegram smoke in this phase.

---

## Changes Made

### 1. `scripts/dev-linux/start-worker.sh` — .env.local sourcing

Added after existing env exports (line ~160):
- Sources `$PROJECT_ROOT/.env.local` via `set -a / source / set +a` (process-scoped only)
- If file exists and TELEGRAM_BOT_TOKEN is set → log "set (not displayed)"
- If file exists but token empty → warn about StubNotifier fallback
- If file missing → warn about StubNotifier fallback
- Token value never printed
- Updated dry-run section and usage doc to mention .env.local
- Worker startup does NOT fail if .env.local is missing

### 2. `apps/telegram-bot/app/handlers/approve_handler.py` — Admin gate

Added at top of `approve_handler()`:
```python
if message.from_user is None:
    await message.answer("⛔ Не удалось определить пользователя.")
    return

user_id = message.from_user.id
admin_ids = settings.admin_user_ids()

if not admin_ids or user_id not in admin_ids:
    await message.answer("⛔ Только администраторы могут подтверждать задачи.")
    return
```

Fail-closed: empty admin list → reject everyone. No API call made if not admin.

### 3. `apps/telegram-bot/app/handlers/reject_handler.py` — Admin gate

Same pattern as approve. Different message text: "отклонять задачи" instead of "подтверждать задачи".

### 4. `apps/worker/tests/test_notifier.py` — Extended (3 → 8 tests)

New tests:
- `test_get_notifier_returns_stub_when_token_empty` — verifies StubNotifier when TELEGRAM_BOT_TOKEN=""
- `test_get_notifier_returns_telegram_when_token_set` — verifies TelegramNotifier when token set
- `test_telegram_notifier_send_success` — mocks httpx, verifies correct API URL and payload
- `test_telegram_notifier_send_failure_does_not_leak_token` — verifies token not in exception
- `test_set_notifier_override` — verifies set_notifier/get_notifier singleton pattern

### 5. `apps/telegram-bot/tests/test_approve_handler.py` — Extended (4 → 8 tests)

Updated existing tests to include `_patch_admin_ids(monkeypatch, [12345])` for admin gate compatibility.

New tests:
- `test_approve_non_admin_rejected` — non-admin gets rejection, API not called
- `test_approve_empty_admin_list_rejects_everyone` — empty admin list = fail-closed
- `test_approve_missing_from_user_rejected` — from_user=None → reject
- `test_approve_admin_can_proceed` — admin passes gate, API is called

### 6. `apps/telegram-bot/tests/test_reject_handler.py` — Extended (4 → 8 tests)

Same pattern as approve tests.

---

## Security Review

| Check | Status |
|-------|--------|
| Token value never printed in logs | ✅ |
| Token value never in test assertions | ✅ |
| .env.local not committed (gitignored) | ✅ |
| SecretRedactionFilter unchanged | ✅ |
| from_user.is_bot guard unchanged | ✅ |
| Admin gate is fail-closed (empty list = reject all) | ✅ |
| No API call if not admin | ✅ |
| .env.local not required for worker startup | ✅ |
| No feedback loop changes | ✅ |
| No live bot started | ✅ |
| No .env/.env.local modified | ✅ |

---

## Validation Results

| Check | Result |
|-------|--------|
| bash -n start-worker.sh | ✅ SYNTAX OK |
| compileall worker app | ✅ OK |
| compileall telegram-bot app | ✅ OK |
| ruff check telegram-bot app | ✅ All checks passed |
| ruff check worker app | ⚠️ 3 pre-existing issues in celery_app.py (WORKER-LINUX-01) |
| pytest worker tests | ✅ 97/98 pass (1 pre-existing path issue) |
| pytest telegram-bot tests | ✅ 75/75 pass |
| pytest test_notifier.py | ✅ 8/8 pass |
| pytest test_approve_handler.py | ✅ 8/8 pass |
| pytest test_reject_handler.py | ✅ 8/8 pass |

---

## Files Changed (6)

1. `scripts/dev-linux/start-worker.sh` — .env.local sourcing
2. `apps/telegram-bot/app/handlers/approve_handler.py` — admin gate
3. `apps/telegram-bot/app/handlers/reject_handler.py` — admin gate
4. `apps/worker/tests/test_notifier.py` — 5 new tests
5. `apps/telegram-bot/tests/test_approve_handler.py` — 4 new tests
6. `apps/telegram-bot/tests/test_reject_handler.py` — 4 new tests

---

## Not Done (by design)

- Live Telegram smoke test (Phase 2)
- Inline keyboard notification with Approve/Reject buttons (future)
- Callback handler admin gate (separate concern)

---

## Next Steps

- TG-05 Phase 2: Live smoke test with real Telegram bot (requires .env.local with real token)
- Verify StubNotifier → TelegramNotifier transition in worker log
- Verify admin gate blocks non-admin in real Telegram chat
