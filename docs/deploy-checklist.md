# Deploy Checklist — DOP-04 Phase 2

Use this checklist for production-intent releases.

---

## A) Before release

- [ ] Change scope approved
- [ ] Release commit identified and pinned
- [ ] `git status --short` reviewed (no unexpected files)
- [ ] API/Bot/Worker tests passed
- [ ] `bash scripts/deploy/validate-production-templates.sh` passed
- [ ] Dry-run preflight completed

---

## B) Env & security

- [ ] `.env` exists at expected server path
- [ ] `.env` permissions are `600` (recommended)
- [ ] Required env keys exist (without printing values)
- [ ] `DEBUG` is not true
- [ ] `SQL_ECHO` is not true
- [ ] API bind is localhost-only
- [ ] No secret values printed in logs/terminal output

---

## C) DB & migrations

- [ ] Migration class assessed (none / backward-compatible / destructive)
- [ ] DB backup completed before migrations
- [ ] Migration approval explicitly granted
- [ ] `CONFIRM_MIGRATIONS=yes` only when approved
- [ ] Rollback path documented (restore preferred for destructive changes)

---

## D) Service restart

- [ ] Restart approval granted (`CONFIRM_SERVICE_RESTART=yes`)
- [ ] Stop order planned: bot → worker → api
- [ ] Start order planned: api → worker → bot
- [ ] Single bot polling instance verified

---

## E) Smoke

- [ ] `/health` returns HTTP 200
- [ ] `/health` contains `status`, `checks`, `database`, `redis`
- [ ] API service status checked
- [ ] Worker service status checked
- [ ] Bot service status checked
- [ ] Optional journal scan reviewed for errors/tracebacks/signature issues

---

## F) Rollback readiness

- [ ] Rollback commit/tag prepared
- [ ] `CONFIRM_ROLLBACK=yes` required before live rollback
- [ ] DB rollback not automatic by default
- [ ] `CONFIRM_DB_ROLLBACK=yes` required for DB rollback path
- [ ] Backup restore instructions available

---

## G) After release

- [ ] Release record written (`WRITE_RELEASE_RECORD=yes` if required)
- [ ] Final smoke completed
- [ ] Incident note added if warnings/failures occurred
- [ ] Memory checkpoint updated (`PROJECT_MEMORY.md`, `.ai_memory/current_state.md`, `.ai_memory/_INDEX.md`, task log)
