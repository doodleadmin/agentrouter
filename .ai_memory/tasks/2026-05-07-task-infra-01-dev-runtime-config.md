# Task: INFRA-01

Дата: 2026-05-07
Агент: studio-orchestrator
Проект: agentrouter

---

## Постановка задачи

Fix two config drift issues discovered during TG-06 Phase 3 live test that required manual workarounds:

1. **CALLBACK_SECRET mismatch:** `start-api-stub.sh` didn't load `.env.local`, so API used empty `CALLBACK_SECRET` while bot used correct secret from `.env.local` → all callbacks rejected. TG-06 workaround: created `~/agentrouter/.env` temp file (since removed).
2. **project.repo_path invalid:** DB had `/opt/agent-control/repos/agentrouter` which doesn't exist on real server. TG-06 workaround: manual `UPDATE projects SET repo_path='/root/agentrouter'`.

Goal: permanent fixes so stub runtime passes without manual DB path fix or temp `.env` workaround.

## Риск-уровень

low

## План

1. Fix A: Add `.env.local` sourcing to `start-api-stub.sh` (same pattern as `start-worker.sh`)
2. Fix B: Create `bootstrap-seed.sh` to ensure project/agent exist in dev DB with correct `repo_path`
3. Validate: bash -n, --dry-run, --help, full test suite, runtime smoke

## Статус

completed

---

## Изменённые файлы

- `scripts/dev-linux/start-api-stub.sh` — modified (+.env.local sourcing block, +report updates)
- `scripts/dev-linux/bootstrap-seed.sh` — NEW file

## Выполненные команды

- `bash -n start-api-stub.sh` → passed
- `bash -n bootstrap-seed.sh` → passed
- `bash bootstrap-seed.sh --dry-run` → passed
- `python -m compileall apps/api/app` → passed
- `ruff check apps/api/app` → passed
- `pytest apps/api/tests -v` → 275/275 ✅
- `pytest apps/worker/tests -v` → 98/98 ✅
- `pytest apps/telegram-bot/tests -v` → 79/79 ✅

## Результаты тестов

passed: 452 (API 275 + Worker 98 + Telegram-bot 79), failed: 0

## Diff summary

- `start-api-stub.sh`: +35 lines (.env.local sourcing, dry-run note, report CALLBACK_SECRET/DATABASE_URL)
- `bootstrap-seed.sh`: +110 lines (NEW: project+agent seeding, idempotent, --dry-run, --help)

## PR

Не создан

---

## Риски, возникшие при выполнении

- **Native psql expected by bootstrap-seed.sh:** script auto-detects Docker vs native psql and uses the right path.
- **Database empty when script runs:** script uses `INSERT ... ON CONFLICT DO UPDATE` — idempotent, safe to run anytime.

## Уроки (Lessons Learned)

- `.env.local` sourcing was already done for `start-worker.sh` (TG-05) but not propagated to `start-api-stub.sh` — process consistency check needed when adding env vars to scripts.
- `project.repo_path` is platform-specific — using `realpath "$PROJECT_ROOT"` eliminates hard-coded path assumptions.

## Следующие шаги

None — INFRA-01 is a self-contained fix. Follow-up tasks would be:
- CI-03: add bootstrap-seed.sh to CI validation pipeline
- CI-04: ensure all runtime scripts have consistent `.env.local` handling

---

## Память обновлена

- [x] PROJECT_MEMORY.md — INFRA-01 entry added
- [x] .ai_memory/current_state.md — INFRA-01 added to completed tasks, count incremented
- [x] .ai_memory/_INDEX.md — task log entry added, count 55→56
