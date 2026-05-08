## Release Workflow — DOP-04 Phase 2

Status: dry-run-first, safety-gated scripts

This workflow defines a **manual, approval-driven** production release process.
Scripts are intentionally safe by default and **do not execute destructive actions unless explicit confirmation flags are provided**.

### Scope

- Included: preflight, release orchestration, rollback orchestration, smoke checks, release records
- Excluded: real VPS deploy automation, CI/CD pipelines, automatic DB restore/downgrade execution

---

## 1) Local checks (before touching server)

1. Ensure working tree is known and reviewable.
2. Verify tests pass (API/Bot/Worker baselines).
3. Verify deploy templates:

```bash
bash scripts/deploy/validate-production-templates.sh
```

4. Run preflight script in dry-run mode:

```bash
DRY_RUN=true ENV_FILE=.env.example PROJECT_ROOT="$PWD" scripts/deploy/preflight.sh
```

---

## 2) Server preflight

Use `preflight.sh` with server paths (manual execution by operator):

```bash
DRY_RUN=true \
PROJECT_ROOT=/opt/agent-control/agentrouter \
ENV_FILE=/opt/agent-control/agentrouter/.env \
EXPECTED_COMMIT=<release-commit> \
scripts/deploy/preflight.sh
```

Checks include:
- required files
- env key presence (without printing values)
- `DEBUG` and `SQL_ECHO` must not be true
- commit visibility and optional commit pin match
- duplicate process warnings (uvicorn/celery/bot polling)
- API bind warning if `0.0.0.0:8000` detected

---

## 3) Deploy orchestration

Run release workflow script.

### Dry-run example (safe default)

```bash
DRY_RUN=true RELEASE_COMMIT="$(git rev-parse HEAD)" scripts/deploy/release.sh
```

### Production-intent manual example (still operator-controlled)

```bash
DRY_RUN=false \
RELEASE_COMMIT=<commit> \
CONFIRM_PRODUCTION_DEPLOY=yes \
CONFIRM_SERVICE_RESTART=yes \
CONFIRM_MIGRATIONS=yes \
ALLOW_GIT_FETCH=yes \
ALLOW_GIT_PULL=no \
ALLOW_CODE_UPDATE=yes \
ALLOW_INSTALL_DEPS=yes \
WRITE_RELEASE_RECORD=yes \
scripts/deploy/release.sh
```

---

## 4) Migrations policy

Migrations are high-risk and require explicit approval.

Classification:

1. **No schema change**
   - no migration required
   - lowest migration risk

2. **Backward-compatible schema change**
   - additive changes (new table/column/index)
   - still requires approval + backup before apply

3. **Schema-breaking/destructive**
   - drop/rename/type change/data rewrite with potential loss
   - requires explicit approval, tested rollback plan, and backup restore strategy

Rules:
- Always backup DB before migrations.
- Prefer restore-from-backup over automatic downgrade for destructive changes.
- Never run migrations silently.

---

## 5) Restart order

Recommended sequence:

1. stop telegram bot (avoid duplicate polling)
2. stop worker
3. restart/start API
4. smoke check API
5. start worker
6. start bot
7. final smoke check

Single polling rule:
- keep exactly one bot polling process active.

---

## 6) Smoke checks

Use script:

```bash
DRY_RUN=true HEALTH_URL=http://127.0.0.1:8000/health scripts/deploy/smoke.sh
```

Optional journal scan:

```bash
DRY_RUN=false CHECK_JOURNAL=true scripts/deploy/smoke.sh
```

Smoke expectations:
- `/health` HTTP 200
- payload contains `status`, `checks`, `database`, `redis`
- no duplicate bot/worker process warnings

---

## 7) Release record

Release/rollback scripts can write metadata records to:

```text
.runtime/releases/YYYYMMDD-HHMMSS-release.txt
.runtime/releases/YYYYMMDD-HHMMSS-rollback.txt
```

Record fields:
- commit
- operator
- timestamp
- dry-run flag
- gate flags used

No secret values are stored.

---

## 8) Approval gates

Human approval is required before:
- production deploy
- migrations
- service restart on production
- rollback execution
- DB rollback execution
- env/secrets changes

Script flags:
- release: `CONFIRM_PRODUCTION_DEPLOY`, `CONFIRM_MIGRATIONS`, `CONFIRM_SERVICE_RESTART`
- rollback: `CONFIRM_ROLLBACK`, `CONFIRM_DB_ROLLBACK`, `CONFIRM_SERVICE_RESTART`

---

## 9) No-secrets and production safety rules

- Never print secret values from `.env`.
- Never `cat .env` in deploy scripts.
- Keep `DEBUG=false` and `SQL_ECHO=false` for production.
- Keep API bound to localhost behind Caddy.
