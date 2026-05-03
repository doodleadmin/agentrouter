---
type: task
task_id: BE-06-docs-fix
status: completed
risk: low
date: '2026-05-04'
agent: backend-architect
---

# Task Summary: BE-06 docs smoke test fix

## Что сделано
- Обновлён `docs/smoke-test-opencode.md` перед BE-06 controlled smoke test.
- Убраны инструкции по изменению основного `.env`.
- Зафиксированы только временные process env overrides:
  - `RUNTIME_PROVIDER=opencode_http`
  - `OPENCODE_SERVER_URL=http://127.0.0.1:3001`
  - `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=true`
- Унифицировано имя временного файла: `.env.opencode-smoke`.
- Зафиксировано требование gitignore для `.env.opencode-smoke`.
- Добавлен явный rollback к default runtime values после smoke test:
  - `RUNTIME_PROVIDER=stub`
  - `OPENCODE_SERVER_URL=""`
  - `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=false`

## Ограничения соблюдены
- Реальный OpenCode server не запускался.
- Код приложения не менялся.
- Deploy/migrations не запускались.
- `.env`/secrets не трогались.
