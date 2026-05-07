# Task: TG-06 Phase 2 — Compact Telegram Callback Protocol

Дата: 2026-05-07
Агент: knowledge-steward
Проект: agentrouter

---

## Постановка задачи

Update project memory after successful TG-06 Phase 2 implementation. Context: compact Telegram callback protocol implemented and validated. Memory update only; do not edit application code, env/secrets, or run live Telegram/OpenCode/deploy/migrations/git push/reset/checkout.

## Риск-уровень

low — memory/documentation update only.

## План

1. Record TG-06 Phase 2 protocol and validation results in `PROJECT_MEMORY.md`.
2. Update `.ai_memory/current_state.md` with current status and completed task entry.
3. Update `.ai_memory/_INDEX.md` task log count and add this task log.
4. Create this task summary in `.ai_memory/tasks/`.

## Статус

completed

---

## Изменённые файлы

- `PROJECT_MEMORY.md` — modified
- `.ai_memory/current_state.md` — modified
- `.ai_memory/_INDEX.md` — modified
- `.ai_memory/tasks/2026-05-07-task-tg06-phase2-compact-callbacks.md` — new

## Выполненные команды

- Не выполнялись.

## Результаты тестов

Implementation validation reported by requester:
- API compileall/ruff/pytest: 275 passed
- telegram-bot compileall/ruff/pytest: 79 passed
- worker compileall/ruff/pytest: 98 passed

No validation commands were run during this memory-only update.

## Diff summary

Memory-only update documenting TG-06 Phase 2 compact callback protocol.

## PR

Не создан.

---

## Implementation context recorded

- Changed implementation files reported: `apps/api/app/routers/tasks.py`; `apps/api/tests/test_tasks_plan_endpoint.py`; `apps/telegram-bot/app/keyboards/__init__.py`; `apps/telegram-bot/app/handlers/callbacks.py`; `apps/telegram-bot/tests/test_callback_handlers.py`; `apps/telegram-bot/tests/test_keyboards.py`.
- Protocol: `v1:<alias>:<task_external_id>:<exp_base36>:<sig16>`.
- Aliases: `a=approve`, `r=reject`, `f=refresh`, `p=show_plan`, `t=show_task`.
- Signing payload: `v1|<alias>|<task_external_id>|<exp_base36>`.
- Signature: HMAC-SHA256 truncated to 16 hex chars.
- Example length: 38 bytes for `task-0004`.
- API behavior: validates compact and legacy formats, validates compact `external_id` match, and finds pending approval by task for approve/reject.
- Bot behavior: inline keyboards use `task.external_id`; callback handlers/status/approve/reject/plan switched to compact callback data.
- Inline reject reason: `Rejected via Telegram inline button`.

## Риски, возникшие при выполнении

Нет. No app code, `.env`, secrets, live services, migrations, deploy, or git remote operations were touched.

## Уроки (Lessons Learned)

Telegram callback data should stay compact and signed; storing `task.external_id` in inline buttons avoids oversized payloads while preserving API-side validation.

## Следующие шаги

- Optional future live smoke for compact inline callbacks when explicitly approved.

---

## Память обновлена

- [x] PROJECT_MEMORY.md
- [x] current_state.md
- [x] _INDEX.md
- [x] task summary
