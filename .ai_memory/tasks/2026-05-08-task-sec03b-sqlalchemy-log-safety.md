# Task: SEC-03B Phase 2 — Decouple SQLAlchemy Echo from DEBUG

**Date:** 2026-05-08  
**Agent:** security-engineer  
**Status:** completed  
**Risk level:** medium (config + log safety, cross-component impact: API config, DB session, dev scripts)

## Goal

Fix the root cause discovered during SEC-03 Phase 3 live smoke: SQLAlchemy engine logger emitted all SQL statements including bind parameters (e.g., `tasks.raw_text` containing user messages with fake-secret test patterns) into `api-stub.log`. The cause was `session.py` using `echo=settings.DEBUG` and dev scripts always setting `DEBUG=true`.

## What was done

### Root cause analysis

The SEC-03 Phase 3 live smoke report noted: *"SQLAlchemy engine logger shows INSERT bind parameters for `tasks.raw_text` — this is the user's original message stored in the task record."*

Investigation traced this to `apps/api/app/db/session.py`:

```python
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, ...)
```

Since all 4 dev scripts (`start-api-stub.sh`, `start-api-opencode.sh`, `start-worker.sh`, `start-telegram-bot.sh`) set `export DEBUG=true`, every dev session was logging full SQL with bind params to stderr/log files.

### Fix

**Config** (`apps/api/app/config.py`):
- Added `SQL_ECHO: bool = False` — new independent config field, defaults to false

**DB Session** (`apps/api/app/db/session.py`):
- Changed `echo=settings.DEBUG` to `echo=settings.SQL_ECHO`

**Dev scripts** (2 of 4 that set DEBUG):
- `scripts/dev-linux/start-api-stub.sh` — added comment: `# SQL_ECHO defaults to false (independent of DEBUG); set SQL_ECHO=true for opt-in SQL logging`
- `scripts/dev-linux/start-api-opencode.sh` — same comment
- `start-worker.sh` and `start-telegram-bot.sh` left unchanged (they don't touch SQLAlchemy)

**Tests** (`apps/api/tests/test_config.py` — NEW):
- `test_sql_echo_defaults_to_false` — verifies default `False`
- `test_sql_echo_independent_of_debug` — verifies DEBUG=true does not affect SQL_ECHO
- `test_sql_echo_opt_in_when_set_true` — verifies explicit `SQL_ECHO=true` works
- `test_default_config_values_consistency` — verifies other defaults unchanged

### Design rationale

```
BEFORE: echo = settings.DEBUG  →  DEBUG=true ⇒ SQL echo ON (always in dev)
AFTER:  echo = settings.SQL_ECHO  →  SQL_ECHO=false by default (never accidental)
```

- **DEBUG** can remain `true` in dev (needed for FastAPI error detail, useful for troubleshooting)
- **SQL_ECHO** defaults to `false` — no SQL bind parameter logging by default
- **SQL echo requires explicit opt-in** — set `SQL_ECHO=true` (process-scoped env or .env.local)
- **No new env vars needed** in `.env` or `.env.example` (defaults cover 100% of use cases)
- **Worker and Bot unaffected** — they don't use `session.py` (worker has its own DB config, bot has no DB)

## Changed files (5)

### MODIFIED (4)
- `apps/api/app/config.py` — added `SQL_ECHO: bool = False`
- `apps/api/app/db/session.py` — `echo=settings.SQL_ECHO` (was `echo=settings.DEBUG`)
- `scripts/dev-linux/start-api-stub.sh` — comment about SQL_ECHO opt-in
- `scripts/dev-linux/start-api-opencode.sh` — comment about SQL_ECHO opt-in

### NEW (1)
- `apps/api/tests/test_config.py` — 4 tests (config defaults, independence, opt-in, consistency)

## Validation

| Component | Tests | Delta |
|-----------|-------|-------|
| API | 397/397 | +4 (was 393) |
| Telegram-bot | 79/79 | 0 |
| Worker | 98/98 | 0 |
| **Total** | **574/574** | **+4** |

- ruff: clean (all 3 packages)
- compileall: clean (all 3 packages)

## Result

✅ SQLAlchemy `echo` fully decoupled from `DEBUG`. SQL bind parameter logging now requires explicit opt-in via `SQL_ECHO=true`. No accidental SQL leakage in dev logs. No regressions. All existing tests pass.

## Open questions

None.

## Follow-up tasks

- SEC-03B Phase 3 (deferred): Consider adding `SQL_ECHO` to worker config + worker DB session if worker ever gets direct SQLAlchemy access (currently worker has no DB session).
- Consider adding uvicorn access log filter to suppress SQLAlchemy engine log lines at INFO level (separate concern, not urgent).

## Memory checkpoint

- **Memory updated:** yes
- **Files updated:** PROJECT_MEMORY.md, .ai_memory/current_state.md, .ai_memory/_INDEX.md, .ai_memory/tasks/2026-05-08-task-sec03b-sqlalchemy-log-safety.md (NEW)
- **Commit hash:** (pending)
- **Skipped reason:** N/A
