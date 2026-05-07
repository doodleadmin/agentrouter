# Task: INFRA-02

Дата: 2026-05-07
Агент: studio-orchestrator
Проект: agentrouter

---

## Постановка задачи

Validate that TG-06 compact callback flow works end-to-end with zero manual workarounds. This is the first live smoke after INFRA-01 fixes (start-api-stub.sh sources .env.local, bootstrap-seed.sh auto-sets repo_path).

Two manual workarounds from TG-06 Phase 3 must be absent:
1. No temporary `~/agentrouter/.env` workaround
2. No manual `UPDATE projects SET repo_path`

## Риск-уровень

low

## План

1. Bootstrap seed (ensure project/agent exist with correct repo_path)
2. Start API stub (verify CALLBACK_SECRET loaded from .env.local)
3. Start worker + bot
4. Create medium-risk task → wait for approval
5. Click inline Approve button → verify compact callback works
6. Validate all checks pass, no manual workarounds

## Статус

completed

---

## Изменённые файлы

No code changes — pure validation/regression smoke.

## Выполненные команды

```bash
# Bootstrap
bash scripts/dev-linux/bootstrap-seed.sh

# Start services
bash scripts/dev-linux/start-api-stub.sh
bash scripts/dev-linux/start-worker.sh
bash scripts/dev-linux/start-telegram-bot.sh

# Smoke
bash scripts/dev-linux/smoke-stub-runtime.sh  # baseline
# Live Telegram: user triggered task, clicked Approve inline button

# Cleanup
bash scripts/dev-linux/cleanup-runtime.sh
```

## Результат

**Verdict: PASS**

- Task: task-0002 (1c39d0a4...)
- Notification delivered to Telegram, message_id: 73
- User clicked inline Approve button
- Callback-answer: 200 OK
- Approve endpoint: 200 OK
- Task final status: approved
- Approval: approved, approved_by=1113930428
- Callback update handled in 370 ms
- Callback data: 38 bytes (limit: 64)

### All Checks Passed

- No BUTTON_DATA_INVALID
- No TelegramBadRequest
- No Invalid callback signature
- No CALLBACK_SECRET mismatch
- No Path-escapes
- No tracebacks
- No duplicate tasks
- No feedback loop
- No token leakage

### What Was Different (vs TG-06 Phase 3)

- No temporary `~/agentrouter/.env` workaround
- No manual `UPDATE projects SET repo_path`
- CALLBACK_SECRET loaded automatically from `.env.local`
- repo_path auto-set by `bootstrap-seed.sh` to `/root/agentrouter`

### Event Timeline

task_created → plan_triggered → plan_generated → approval_requested → callback_received → approval_granted

### Verdict

TG-06 compact inline callback protocol is production-viable with zero manual workarounds.
INFRA-01 fixes confirmed working.

---

## Открытые вопросы

None.

## Следующие задачи

None — INFRA-02 is a closeout validation.
