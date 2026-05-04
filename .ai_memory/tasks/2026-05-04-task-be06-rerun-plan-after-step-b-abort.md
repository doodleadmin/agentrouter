---
type: task
task_id: BE-06
status: completed
risk: low
requires_approval: false
date: '2026-05-04'
agent: knowledge-steward
---

# BE-06: Rerun plan after Step-B abort

## Date/Time
- Date: 2026-05-04
- Time: not captured (documentation-only update)

## Agent
- knowledge-steward

## Goal
- Зафиксировать причины abort на Step-B и выровнять rerun-процедуру BE-06 в документации/памяти без запуска серверов и без изменения кода.

## Abort causes (summary)
1. Невалидная/устаревшая ориентация на порт `3001` для rerun.
2. Неоднозначность команды старта OpenCode (альтернативные launch варианты вместо единственного канонического).
3. Недостаточно явные identity checks для подтверждения целевого runtime (`/global/health`, `/doc`).
4. Неявная compatibility-проверка backend transport контракта (`POST /sessions`, `GET /sessions/{id}/events`).

## Corrected rerun procedure
- Использовать только `opencode serve --port <PORT> --hostname 127.0.0.1`.
- Port strategy: primary `4096`, fallback `4097`.
- Health endpoint: `GET http://127.0.0.1:<PORT>/global/health`.
- Identity checks: required `/global/health` и `/doc`; optional `/config` или `/agent`.
- Явные запреты: `opencode/server`, `@opencode/server`, bind на `0.0.0.0`.
- Только process env overrides; main `.env` не трогать; optional `.env.opencode-smoke` (gitignored, temporary).
- Cleanup invariant: вернуть `RUNTIME_PROVIDER=stub`, `OPENCODE_SERVER_URL=""`, `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=false`.

## Changed files
- `docs/smoke-test-opencode.md`
- `.ai_memory/tasks/2026-05-04-task-be06-controlled-smoke-test-plan.md`
- `.ai_memory/_INDEX.md`
- `.ai_memory/current_state.md`
- `PROJECT_MEMORY.md`

## Result
- Документация и memory notes синхронизированы под BE-06 rerun-plan reality.
- Создан отдельный task log по abort + corrected rerun path.
- Код, `.env`, runtime конфиги и инфраструктура не изменялись.

## Open questions
- Нужно ли зафиксировать canonical expected response shape для `/doc` в отдельном контрактном документе?

## Follow-up tasks
1. При следующем execution-approve: выполнить только preflight probes без интеграционного task-run.
2. После preflight: добавить отдельный evidence-log с фактическими HTTP статусами/response snippets (без чувствительных данных).
