# current_state.md — Текущий активный статус

Обновлено: 2026-05-09 (VPS-03B: env + DB/Redis bootstrap only) | Автор: devops-automator

---

## Статус проекта

**Current state:** MVP v1 COMPLETE
**Latest stable commit:** `7f51829` (pushed to `doodleadmin/agentrouter`)
**Test baseline:** API 401/401, Bot 79/79, Worker 98/98 — Total 578/578 PASS
**Production deploy:** NOT executed — requires explicit approval
**Security chain:** SEC-01..SEC-03B — all PASS
**Deploy readiness:** DOP-03 + DOP-04 — dry-run validated

**Фаза:** MVP v1 complete (Phase 0–4, Phase 6–7 dry-run validated)
**Состояние:** FND-01..03, DOP-01..04, BE-01..12, TG-01..06, MEM-01..04, WRK-01..04, SEC-01..03B, CI-01..02, INFRA-01..02, DEV-LINUX-01..01D, WORKER-LINUX-01, DEV-DB-01 выполнены. All CRITICAL/HIGH closed. 87 task logs.
**Блокеры:** Нет (all original blockers resolved)
**Критические проблемы:** Нет

## Что происходит сейчас

- VPS-03B (devops-automator): на VPS `45.130.213.12` выполнен безопасный bootstrap только для infra-зависимостей — создан production `.env` из `.env.example` (бывш. absent), сгенерированы `POSTGRES_PASSWORD` + `CALLBACK_SECRET` (значения не выводились), права `.env` `600` owner `agentmc`; `docker compose config` (prod) PASS и рендер в `/tmp/agentrouter-compose-rendered.yml`; запущены только `postgres` и `redis`, readiness PASS (`pg_isready`, `PONG`); подтверждено отсутствие запуска `api/worker/telegram-bot`, отсутствие deploy/migrations/OpenCode, порт 8000 не слушается, 80/443 закрыты, UFW без изменений (только 22/tcp).

- FND-01 (git-workflow-master): .gitignore, CHANGELOG, CONTRIBUTING созданы
- FND-02 (backend-architect): FastAPI app, /health, pydantic-settings config созданы
- FND-03 (backend-architect): SQLAlchemy модели + Alembic baseline созданы
- DOP-01 (devops-automator): dev docker-compose создан (postgres+redis+api)
- DOP-01 check (devops-automator): `docker compose config/up/ps/logs` для postgres+redis выполнены успешно
- FND-03 fix (backend-architect): `pyproject.toml` исправлен (`[tool]` → `[build-system]` + hatch build config)
- FND-03 verification (backend-architect): `compileall` ok, `alembic history` ok, `alembic upgrade head --sql` ok (8 tables, vector extension, ivfflat)
- BE-01 (backend-architect): CRUD endpoints /projects, /agents, /telegram/topics созданы (schemas + services + routers + tests)
- BE-02 (backend-architect): Tasks + Approvals + TaskEvents domain созданы (14+10+2 endpoints, 41 тест пройден)
- TG-01 (backend-architect): Telegram bot gateway создан (commands + topic-aware task creation)
- TG-02 (backend-architect): `/bind_topic`, `/unbind_topic`, `/topic_status` + routing bridge
- BE-03 (backend-architect): runtime adapter plan-only + endpoint `/runtime/tasks/{task_id}/plan`
- WRK-01 (backend-architect): Celery worker skeleton с 7 очередями, healthcheck, stub-задачи, retry/backoff
- WRK-02 (backend-architect): Plan pipeline — trigger-plan endpoint, agent_plan + notifications с Notifier adapter, Telegram bot integration
- MEM-01 (knowledge-steward): Memory provisioning service, 5 templates, docs/memory-system.md, forbidden content detection
- MEM-02 (backend-architect): Memory CRUD API — 6 endpoints, policy service (access tiers + secrets guard), 76 новых тестов
- MEM-03 (backend-architect): Memory indexing + retrieval — chunking, deterministic embeddings, `/memory/reindex`, `/memory/search`, worker memory_index API trigger
- DOP-02 (devops-automator): Dockerfiles + sandbox compose — non-root, no-new-privileges, read_only, isolated internal network, resource limits
- Security review (security-engineer): WRK-03 допустим только при mandatory guardrails; устранена несостыковка policy (staging deploy = approval_required)
- WRK-03 (backend-architect): Safe execute pipeline — approved-only gate, command/worktree policy, fake sandbox runner, audit events, redaction
- WRK-03-hardening (backend-architect): CRITICAL/HIGH закрыты — shell escape, chaining operators, event_type validation, network/privesc tools
- WRK-03 fake E2E (backend-architect): оба сценария подтверждены через FakeSandboxRunner (success + blocked), transitions/events/redaction/result_summary проверены
- WRK-04 (backend-architect): DockerSandboxRunner реализован как opt-in adapter (argv-only, dynamic task-worktree mount, timeout, cleanup, redaction, config-driven limits), FakeSandboxRunner остался default
- WRK-04-polish (backend-architect): закрыты medium/low замечания review (cleanup failure test, docker unavailable unit test + redaction, dynamic result_summary, docs checklist)
- WRK-04 manual local backend test (backend-architect): сценарии A-E подтверждены локально через worker execute pipeline + DockerSandboxRunner evidence; перед/после теста подтверждён `SANDBOX_RUNNER_MODE=fake`, временный docker override только в процессе теста
- WRK-04 real docker smoke test (backend-architect): Scenario A выполнен с реальным контейнером; команда `python -m compileall .`, `exit_code=0`, single mount policy подтверждён (`manual-test-wrk04 -> /workspace`), cleanup completed, режим возвращён в `fake`
- WRK-04 manual-test hardening (backend-architect): `manual-test-*` worktree prefix теперь разрешён только при `SANDBOX_MANUAL_TEST_MODE=True`; в normal mode только `task-*`; path traversal всегда отклонён; 5 новых тестов; `FakeSandboxRunner` остаётся default
- BE-04 transport hardening (backend-architect): удалён hidden fallback на fake transport для `opencode_http`; default provider=`stub`; unknown provider и missing `OPENCODE_SERVER_URL` теперь fail-closed (`runtime_error` + `task_failed`); fake transport только через explicit DI в тестах; `pytest tests -v` passed
- BE-05 RealOpenCodeHttpTransport + gap closures (backend-architect): реализован RealOpenCodeHttpTransport (HTTP/SSE на httpx), закрыты 3 gaps (max_plan_size 100KB truncation, session/idle timeout enforcement, tool.call path confinement), SSE robustness улучшена, docs/smoke-test-opencode.md создан, 197/197 tests passed; real OpenCode server не запускался
- BE-05 Phase 1 hardening (backend-architect): закрыты B-1 (test adaptation), M-1 (_truncate_plan session_id), M-2 (SSE non-JSON chunk 64KB limit), M-3 (RUNTIME_ALLOW_REAL_OPENCODE_HTTP safety gate, default=False). 205/205 tests passed. Default=stub подтверждён.
- BE-06 preflight plan (studio-orchestrator): подготовлен controlled smoke test plan-only checklist для real OpenCode HTTP adapter (localhost:3001), включая временные env overrides через environment variables (без изменения .env), safe low-risk prompt, abort criteria, post-smoke validation. Ничего не запускалось.
- BE-06 docs fix (backend-architect): обновлён `docs/smoke-test-opencode.md` — убраны инструкции изменения основного `.env`, зафиксированы только process env overrides (`RUNTIME_PROVIDER`, `OPENCODE_SERVER_URL`, `RUNTIME_ALLOW_REAL_OPENCODE_HTTP`), унифицирован `.env.opencode-smoke`, добавлен явный rollback к defaults (`stub`, empty URL, allow=false).
- BE-06 rerun-plan update (knowledge-steward): документация и memory выровнены после Step-B abort — портовая стратегия `4096` (fallback `4097`), only `opencode serve --port <PORT> --hostname 127.0.0.1`, identity checks (`/global/health`, `/doc`, optional `/config`/`/agent`), backend compatibility preflight (`POST /session`, `POST /session/{id}/message`), explicit запреты (`opencode/server`, `@opencode/server`, `0.0.0.0`).
- BE-06 transport compatibility fix (backend-architect + security-engineer): runtime transport переведён на актуальный sync contract `POST /session` + `POST /session/{id}/message`; mapping `parts -> plan.delta/plan.final/tool.call` с fail-closed для unknown/malformed; сохранены guardrails и policy boundaries; закрыт timeout hang risk через bounded default read timeout; итог security verdict: PASSED.
- BE-06 task creation fix (backend-architect): устранены non-persisting writes и FK 500 — выставлена корректная transaction boundary (commit/rollback в request scope), `IntegrityError` маппится в безопасные HTTP ответы (`422` для FK `23503`, `409` для conflict/violation); подтверждён rollback после ошибки и сохранность успешных POST.
- BE-06 FINAL EXECUTION (backend-architect + studio-orchestrator): Controlled smoke test с real OpenCode 1.14.33 (Steps A–G). Provider wiring, RealOpenCodeHttpTransport, session creation (`POST /session` → `201`) подтверждены. `POST /session/{id}/message` → `400 Bad Request` (payload contract mismatch) обработан fail-closed (`runtime_error` → `task_failed`). No bypass, no leaks, no file changes. Интеграционная находка: BE-07 follow-up для contract alignment.
- BE-07 payload contract alignment (backend-architect): для `POST /session/{id}/message` принят минимальный payload `{ "message": <text> }` вместо legacy extra-fields; клиентский mapping обновлён под `parts` и `content` с fail-closed на empty/malformed/unknown. Guardrails сохранены (plan-only, policy_blocked mutating tool.call, path confinement, redaction upper layers, max_plan_size, timeout, no silent fallback). Архитектурный блокер снят: policy-layer dependency убрана из `transport.py` (transport-only). Валидация: compileall + ruff + pytest `204 passed`. Реальный OpenCode server не запускался.
- DEV-DB-01 (backend-architect): исправлен sync/async engine mismatch в `apps/api/alembic/env.py` — `engine_from_config()` заменён на `create_async_engine()` + `asyncio.run()`, добавлена валидация безопасности `_validate_migration_safety()`. Онлайн-миграция НЕ запускалась (только `--sql`). 219/219 тестов пройдено.
- BE-07+ native contract alignment (backend-architect): payload для `POST /session/{id}/message` переведён на OpenCode 1.14.33 native формат `{"parts": [{"type": "text", "text": "..."}]}` (schemas: `OpenCodeSessionTextPart`). Client `_map_message_response_to_events` переписан под native part-type dispatch: `text→plan.delta`, `reasoning→SKIPPED` (never stored), `step-start→skipped`, `step-finish(reason=stop)→plan.final`, `tool→tool.call`, `unknown→runtime_event_malformed` (fail-closed). Security GO (8 checks), Architecture GO (5 rules). Валидация: compileall + ruff + pytest `219 passed` (+12 новых тестов). Real OpenCode server не запускался.
- BE-08 session traceability + timeout tuning (backend-architect): `POST /session` payload теперь `{"title": "<task title>"}` — единственное поле, принимаемое OpenCode 1.14.33. Добавлен `OpenCodeSessionCreateRequest` schema, поле `task_title` в `RuntimePlanContext`. Удалены игнорируемые поля (mode/correlation_id/idempotency_key/input). `RUNTIME_SESSION_TIMEOUT_SECONDS` увеличен 60→180. Session contract обновлён в docs. Guardrails сохранены (stub default, fail-closed, path confinement, redaction, max_plan_size, plan-only). Test: 225 collected, 224 passed, 1 pre-existing data-collision. Real OpenCode не запускался.
- BE-08 REAL OpenCode smoke SUCCESS (backend-architect + studio-orchestrator): First successful end-to-end plan_generated from real OpenCode 1.14.33. session_id=`ses_20bbf3443ffe9jGPUiUrGNkS7G`, plan_text=875 chars (real analysis, no stub fingerprints). Single retry at ~180s (borderline timeout) then success. All guardrails held: no file mutation, no command execution, no sandbox events, no secret leakage, localhost-only. Follow-up recommended: increase timeout 180→300s. OpenCode stopped, API returned to stub mode, git clean.
- BE-09 Phase 1 (backend-architect): Worker `API_TIMEOUT_SECONDS` увеличен 30→300 (>= RUNTIME_SESSION_TIMEOUT_SECONDS=180 + buffer для 80-170s real OpenCode plans). 2 новых теста. 91/91 worker tests pass. API guardrails не трогались (stub default, allow=false, OpenCode не запускался).
- BE-10 Runtime Reliability Hardening (backend-architect): 6 изменений — P0-1 (idempotency guard CREATED→PLANNING via TaskService.update_status), P0-2 (trigger-plan 409 gate), P1-3 (notification isolation в worker), P1-4 (retry OpenCodeTimeoutError/OpenCodeConnectionError), P2-5 (runtime_session_created до retry loop), P2-6 (RUNTIME_SESSION_TIMEOUT 180→300, API_TIMEOUT 300→420). Reviews: Security 6/6 PASS, Architecture 5/5 PASS, Reality-check 6/6 PASS. 237/237 API tests pass, 93/93 worker tests pass. Real OpenCode не запускался, provider=stub, allow=false.

## Активные задачи

| Задача | Статус | Агент |
|--------|--------|-------|
| FND-01: Repo Bootstrap | ✅ Выполнена | studio-orchestrator |
| FND-02: API Skeleton | ✅ Выполнена | studio-orchestrator |
| FND-03: DB Foundation | ✅ Выполнена | backend-architect |
| DOP-01: Dev Docker Compose | ✅ Выполнена | devops-automator |
| DOP-01: Safe Local Check | ✅ Выполнена | devops-automator |
| FND-03: pyproject.toml fix + alembic verify | ✅ Выполнена | backend-architect |
| BE-01: CRUD Endpoints | ✅ Выполнена | backend-architect |
| BE-02: Tasks + Approvals | ✅ Выполнена | backend-architect |
| TG-01: Telegram Bot Gateway | ✅ Выполнена | backend-architect |
| TG-02: Topic Binding + Routing | ✅ Выполнена | backend-architect |
| BE-03: Runtime Adapter (plan-only) | ✅ Выполнена | backend-architect |
| WRK-01: Celery Worker Skeleton | ✅ Выполнена | backend-architect |
| WRK-02: Plan Pipeline | ✅ Выполнена | backend-architect |
| MEM-01: Memory Provisioning | ✅ Выполнена | knowledge-steward |
| MEM-02: Memory CRUD API | ✅ Выполнена | backend-architect |
| MEM-03: Memory Indexing + Retrieval | ✅ Выполнена | backend-architect |
| DOP-02: Dockerfiles + Sandbox Compose | ✅ Выполнена | devops-automator |
| Security Review before WRK-03 | ✅ Выполнена | security-engineer |
| WRK-03: Safe Execute Pipeline | ✅ Выполнена | backend-architect |
| WRK-03-hardening: Security Hardening | ✅ Выполнена | backend-architect |
| WRK-03 Fake E2E | ✅ Выполнена | backend-architect |
| WRK-04: DockerSandboxRunner (opt-in) | ✅ Выполнена | backend-architect |
| WRK-04-polish: Pre-manual-test hardening | ✅ Выполнена | backend-architect |
| WRK-04: Manual local backend test | ✅ Выполнена | backend-architect |
| WRK-04: REAL Docker smoke test (Scenario A) | ✅ Выполнена | backend-architect |
| WRK-04: manual-test hardening | ✅ Выполнена | backend-architect |
| BE-04: transport hardening | ✅ Выполнена | backend-architect |
| BE-05: RealOpenCodeHttpTransport + gap closures | ✅ Выполнена | backend-architect |
| BE-05 Phase 1 hardening (B-1+M-1/M-2/M-3) | ✅ Выполнена | backend-architect |
| BE-06: Final Execution (real OpenCode smoke test) | ✅ Выполнена | backend-architect + studio-orchestrator |
| BE-07: Payload contract alignment | ✅ Выполнена | backend-architect |
| BE-07+: Native contract alignment (OpenCode 1.14.33) | ✅ Выполнена | backend-architect |
| BE-08: Session traceability + timeout tuning | ✅ Выполнена | backend-architect |
| BE-08-real: OpenCode smoke SUCCESS (first real plan_generated) | ✅ Выполнена | backend-architect + studio-orchestrator |
| BE-09 Phase 1: Worker API timeout fix (30→300) | ✅ Выполнена | backend-architect |
| DEV-DB-01: Fix Alembic async/sync engine mismatch | ✅ Выполнена | backend-architect |
| BE-11: Runtime Runbook + Local Smoke Automation | ✅ Выполнена | devops-automator + knowledge-steward |
| BE-12: OpenCode Read-Timeout Alignment | ✅ Выполнена | backend-architect |
| BE-11: Scripts Final Repair (parse/dry-run PASS) | ✅ Выполнена | studio-orchestrator |
| TG-03: Telegram Approvals + Task Status UX | ✅ Выполнена | backend-architect |
| TG-04: Live Integration Phase 1 (security prereqs) | ✅ Выполнена | security-engineer + backend-architect |
| TG-04: HTML Placeholder Fix | ✅ Выполнена | studio-orchestrator |
| TG-04: Private Chat Wording Fix | ✅ Выполнена | studio-orchestrator |
| TG-04: Private Chat Binding Support | ✅ Выполнена | studio-orchestrator |
| DEV-LINUX-01: Ubuntu 22.04 Runtime Scripts | ✅ Выполнена | studio-orchestrator |
| DEV-LINUX-01B: Dry-Run Precondition Fix | ✅ Выполнена | studio-orchestrator |
| DEV-LINUX-01C: Real Stub Contour Validation | ✅ Выполнена | studio-orchestrator |
| DEV-LINUX-01D: Real OpenCode Runtime Contour | ✅ Выполнена | studio-orchestrator |
| WORKER-LINUX-01: Celery SIGHUP Restart Fix | ✅ Выполнена | studio-orchestrator |
| TG-04 Phase 5: Live Private Chat E2E | ✅ Выполнена | studio-orchestrator |
| TG-06 Phase 2: Compact Telegram Callback Protocol | ✅ Выполнена | studio-orchestrator |
| TG-06 Phase 3: Live Callback E2E | ✅ Выполнена | studio-orchestrator |
| INFRA-01: Dev Runtime Config Drift Fix | ✅ Выполнена | studio-orchestrator |
| INFRA-02: TG-06 Regression Live Smoke | ✅ Выполнена | studio-orchestrator |
| MEM-04 Phase 2: Soft Mandatory Memory Checkpoints | ✅ Выполнена | knowledge-steward |
| SEC-01 Phase 2: Permission Engine MVP | ✅ Выполнена | security-engineer |
| SEC-01 Phase 3: Live Smoke — Admin Gate Validation | ✅ Выполнена | security-engineer |
| SEC-02 Phase 2: Audit Model, Migration & Service | ✅ Выполнена | security-engineer |
| SEC-02 Phase 3: P0 Audit Integration | ✅ Выполнена | security-engineer |
| SEC-02 Phase 4: Live Smoke — Audit Trail Validation | ✅ Выполнена | security-engineer |
| SEC-03 Phase 2: Centralized Secrets Redaction | ✅ Выполнена | security-engineer |
| SEC-03 Phase 3: Live Redaction Smoke | ✅ Выполнена | security-engineer |
| SEC-03B Phase 2: SQLAlchemy Log Safety | ✅ Выполнена | security-engineer |
| DOP-03 Phase 2: Production Runtime Templates + Enhanced Health Check | ✅ Выполнена | studio-orchestrator |
| DOP-03 Phase 3: Production Templates Dry-run Validation | ✅ Выполнена | studio-orchestrator |
| DOP-04 Phase 2: Safe Release/Rollback Workflow Artifacts (memory) | ✅ Выполнена | knowledge-steward |
| DOP-04 Phase 3: Release Workflow Dry-run Validation | ✅ Выполнена | studio-orchestrator |
| VPS-01: Server Preflight Inspection (45.130.213.12) | ✅ Выполнена | studio-orchestrator |
| VPS-02: Base Server Setup (45.130.213.12) | ✅ Выполнена | studio-orchestrator |

- **SEC-03B Phase 2 SQLAlchemy Log Safety (security-engineer):** Decoupled SQLAlchemy `echo` from `DEBUG` config. Root cause from SEC-03 Phase 3 live smoke: `session.py` used `echo=settings.DEBUG`, dev scripts always set `DEBUG=true`, causing SQLAlchemy engine logger to emit all SQL + bind params (including `tasks.raw_text`) into `api-stub.log`. Fix: added `SQL_ECHO: bool = False` to config (independent of DEBUG), changed `session.py` to use `echo=settings.SQL_ECHO`, updated 2 dev-linux scripts with opt-in comments. Design: DEBUG can remain true in dev (FastAPI error detail), SQL_ECHO defaults to false (no bind param logging), SQL echo requires explicit `SQL_ECHO=true`. Validation: API 397/397 (was 393, +4 config tests), Bot 79/79, Worker 98/98, Total 574/574, ruff clean, compileall clean. 5 files changed (4 modified + 1 new).

- **DOP-03 Phase 2 Production Runtime Templates + Enhanced Health Check (studio-orchestrator):** Created production deployment infrastructure. Enhanced /health endpoint with backward-compatible DB (SELECT 1) and Redis (ping) dependency checks — returns `status: "ok"/"degraded"`, HTTP 200 always. Created Caddyfile template (domain/TLS placeholders, 127.0.0.1 proxy). Created 3 systemd unit templates (api on 127.0.0.1:8000, worker with celery, bot with python -m app.main; all NoNewPrivileges, ProtectSystem=strict, User=agentmc). Created docker-compose.prod.yml (postgres+redis internal, API 127.0.0.1:8000 only, DEBUG=false, SQL_ECHO=false). Created .env.example with CHANGE_ME placeholders. Created validate-production-templates.sh (9 safety checks, ALL CHECKS PASSED). Created docs/deployment.md (architecture, two deploy modes, env setup, permissions, startup order, rollback). Created docs/operations-runbook.md (start/stop/restart, logs, health monitoring, DB operations, "What NOT to Do"). Updated infra/deploy/README.md. Validation: API 401/401 (+4 health tests), Bot 79/79, Worker 98/98, Total 578/578, ruff clean, compileall clean, deploy validation ALL CHECKS PASSED. 14 files changed (2 modified + 12 new).

- **DOP-03 Phase 3 Production Templates Dry-run Validation (studio-orchestrator):** Validated production templates on WSL2 without deploy. Synced WSL repo to Windows `09b626e`. `validate-production-templates.sh` returned ALL CHECKS PASSED. Manual safety greps found no dangerous production matches (SQL_ECHO/DEBUG only in validation/docs warnings; `0.0.0.0` only in dev compose). Docker prod config render PASS (`DEBUG=false`, `SQL_ECHO=false`, API bind `127.0.0.1`, DB/Redis internal-only, placeholders only). systemd-analyze showed only environment-specific warnings for missing deploy paths in WSL (no syntax failures). Caddy binary unavailable in WSL (SKIP with reason). Runtime smoke PASS: `/health` 200 with api/database/redis all `ok`, no secrets in response. API logs showed `CALLBACK_SECRET` redacted and no SQL bind parameter dumps. Regression suite PASS: API 401/401, Bot 79/79, Worker 98/98 (total 578/578), compileall/ruff clean. Cleanup PASS: no orphan api process, git clean, `.env` absent, `.env.local` gitignored. Verdict: PASS/GO for dry-run readiness.

- **DOP-04 Phase 2 Release Workflow artifacts (studio-orchestrator + devops/security coordination):** Implemented safe deploy workflow artifacts. New scripts under `scripts/deploy/`: `preflight.sh`, `release.sh`, `rollback.sh`, `smoke.sh` (all default `DRY_RUN=true`). Added explicit confirmation gates: release (`CONFIRM_PRODUCTION_DEPLOY`, `CONFIRM_MIGRATIONS`, `CONFIRM_SERVICE_RESTART`), rollback (`CONFIRM_ROLLBACK`, `CONFIRM_DB_ROLLBACK`, `CONFIRM_SERVICE_RESTART`), plus mandatory `RELEASE_COMMIT`/`ROLLBACK_COMMIT`. `preflight.sh` checks required files/env keys, warns on permissive env perms, blocks `.env/.env.local` scripted usage, verifies git status/commit and optional `EXPECTED_COMMIT`, checks duplicate uvicorn/celery/bot processes, warns on `0.0.0.0:8000`, and can run template validation outside dry-run. `smoke.sh` validates `/health` structure, checks service states, warns on duplicate polling/worker processes, optional journal scan (`CHECK_JOURNAL=true`) with counters only (traceback/error/button/callback-signature/sql-bind indicators), no raw secret output. Updated docs: `docs/release-workflow.md`, `docs/deploy-checklist.md`, `docs/deployment.md`, `docs/operations-runbook.md`, `infra/deploy/README.md`. Validation: `bash -n` all deploy scripts PASS, `validate-production-templates.sh` PASS (new checks for script existence/safety flags/gates), dry-run commands PASS, regression tests PASS (API 401/401, Bot 79/79, Worker 98/98; total 578/578). No deploy/migrations/live Telegram/OpenCode/push executed. No secrets printed.

- **DOP-04 Phase 3 Release Workflow Dry-run Validation (studio-orchestrator):** End-to-end dry-run validation executed on commit `9187297` in WSL2. WSL synchronized from Windows local repo; git clean baseline confirmed. Static syntax checks PASS for deploy scripts and validator. `validate-production-templates.sh` returned `ALL CHECKS PASSED` (including DRY_RUN defaults, release/rollback gates, no DEBUG/SQL_ECHO unsafe defaults, no inline secrets). Safety grep checks found no real Telegram tokens, no DB/Redis credential URLs, and no `cat .env` usage; one historical fake callback secret remained only in old memory log and marked fake. `preflight.sh` dry-run PASS (29 PASS / 3 WARN / 0 FAIL). Local API stub smoke PASS (`/health` HTTP 200 with checks.api/database/redis=`ok`, no secrets in response). `smoke.sh`, `release.sh`, and `rollback.sh` dry-runs PASS with no live actions. Negative gate checks with `DRY_RUN=false` verified fail-closed behavior: release refused without `CONFIRM_PRODUCTION_DEPLOY=yes`, rollback refused without `CONFIRM_ROLLBACK=yes`; no actions executed. Regression tests PASS: API 401/401, Bot 79/79, Worker 98/98 (total 578/578), compileall/ruff clean. Cleanup completed; auto-restarted API from cleanup script was manually stopped; no orphan uvicorn from this run; `.env` absent; `.env.local` unchanged/gitignored.

- **SEC-03 Phase 2 Centralized Secrets Redaction (security-engineer):** Created centralized redaction module `apps/api/app/security/redaction.py` with 5 functions covering 10 secret pattern types. Unified 4 previously separate redaction systems (audit service, runtime guardrails, task events, worker) into one source of truth. All redacted values → `[REDACTED:TYPE]`. Marker format: `[REDACTED:TYPE]`. Coverage: Telegram token, Bearer, JWT, sk-* API key, GitHub token, DB/Redis passwords, generic assignments, PEM private key, CALLBACK_SECRET. Audit service: removed local redact_text/sanitize_metadata (~70 lines). Runtime guardrails: redact_payload delegates to redact_mapping. Task events: redact_mapping(payload) before INSERT. Worker: synced 10-pattern set. Not changed (out of scope): MemoryPolicyService (keeps REJECT), pre-commit hooks, git history scan, uvicorn logging filter, .env/secrets. Validation: API 393/393 (+46 new redaction tests), Bot 79/79, Worker 98/98, Total 570/570, ruff clean, compileall clean. 12 files changed (2 new, 10 modified).

- **SEC-03 Phase 3 Live Redaction Smoke (security-engineer):** Verified centralized redaction (Phase 2) against a controlled fake-secret corpus injected into real task/approval/audit flows. Live contour: WSL Ubuntu 22.04, Docker PostgreSQL + Redis, commit 5025168, DB re-initialized (alembic 0001+0002), seed restored. Task dfee2c8f (medium risk) created → plan → waiting_approval → user /approve → approved. 8 fake-secret patterns injected in task raw_text (Telegram token, Bearer, OpenAI sk-*, GitHub ghp_*, DB password, Redis password, generic assignment, CALLBACK_SECRET). Results: security_audit_events.metadata PASS, security_audit_events.reason PASS, Worker log PASS (0 fake secrets), Bot log PASS (0 fake secrets), task_events payload PASS. SQLAlchemy engine INSERT bind parameters for tasks.raw_text expected (user input stored in task record). 8 pre-existing [REDACTED] markers in Worker log from prior sessions. Verdict: PASS — centralized redaction protects all auditable surfaces. No code changes. No secrets exposed. 0 files changed (memory-only).

- **SEC-02 Phase 3 P0 Audit Integration (security-engineer):** Wired SecurityAuditService into 4 P0 security-sensitive API endpoints (approve, reject, callback-answer). Two event types: `permission_denied` + `approval_decided` for approve/reject; `callback_validated` allowed/denied (6 failure types) for callback-answer. Best-effort writes (never blocks primary flow). No raw callback_data in metadata. Reason redacted. Task FK safety preserved. Changed files: audit_service.py (+57), approvals.py (+66), tasks.py (+156), test_security_audit_integration.py (NEW, 16 tests). Validation: API 347/347 (was 331), Bot 79/79, Worker 98/98, Total 524/524, ruff clean, compileall clean. No DB changes/migrations. No deploy/secrets/OpenCode.

- **SEC-02 Phase 4 Live Smoke: Audit Trail Validation (security-engineer):** Validated SecurityAuditService audit trail against real Telegram /approve flow. Live contour: WSL Ubuntu 22.04, commit 7ae7f6c, DB re-initialized (alembic 0001+0002), seed restored. Task task-0001 (88194932, medium risk) created → plan → waiting_approval. Approval a90f100c created. User /approve → task approved. DB verified: audit event `approval_decided` / allowed / `SEC-PERM-APPROVE-ALLOW` written to `security_audit_events`. All fields correct: actor_type=user, actor_id=1113930428, source=telegram, task_id=88194932, approval_id=a90f100c. Metadata clean (no secrets). Reason empty (no redaction needed). Old task_events co-exists (task_created, plan_triggered, plan_generated, approval_requested, approval_granted). Bot: 4/4 HTTP 200. Worker: stale session errors pre-existing, not from test. Verdict: PASS — audit trail validated for real Telegram flows. No code changes. No secrets exposed.

- **BE-12 OpenCode read-timeout alignment (backend-architect):** `send_message()` локальный `httpx.AsyncClient` с `read=None` (SDK-aligned). `create_session()` bounded. Error mapping сохранён. Guardrails нетронуты. 16/16 transport tests pass (+5 BE-12). 251/252 full suite pass. Real OpenCode не запускался.
- **TG-03 Telegram Approvals + Task Status UX (backend-architect):** 7 phases complete. API: 409 for already-decided (was 422), GET /tasks/{id}/plan, POST /tasks/{id}/callback-answer with HMAC-signed callback validation. Bot: /status, /plan, /approve, /reject commands + inline keyboards (approve/reject/show-plan/refresh) + callback handler with API-side validation. API client extended (8 new methods). Formatters (task cards, approval cards, plan excerpts). Tests: 35/35 bot tests + 11 API tests pass (1 pre-existing flake).

- **TG-06 Phase 2 Compact Telegram Callback Protocol (studio-orchestrator):** Inline callback data switched to compact signed format `v1:<alias>:<task_external_id>:<exp_base36>:<sig16>` with aliases `a/r/f/p/t` for approve/reject/refresh/show_plan/show_task. Signing payload is `v1|<alias>|<task_external_id>|<exp_base36>`, HMAC-SHA256 truncated to 16 hex. API validates compact and legacy formats, checks compact external_id match, and resolves pending approval by task for approve/reject. Bot inline keyboards now use `task.external_id`; callback handlers/status/approve/reject/plan updated. Reject reason: `Rejected via Telegram inline button`. Validation: API 275 passed, telegram-bot 79 passed, worker 98 passed. No live Telegram/OpenCode/deploy/migrations/git push/reset/checkout; no `.env`/secrets changed.

- **TG-06 Phase 3 Live Compact Callback E2E (studio-orchestrator):** Compact callback protocol validated end-to-end with live inline button interaction. Medium-risk task (task-0002) created via worker → plan generated → approval fb8f305a created → user clicked Approve inline button → callback data 38 bytes (under 64-byte limit) → callback validation POST /callback-answer 200 action_valid=true → approve flow POST /approvals/{id}/approve 200 → task waiting_approval→approved, approval pending→approved approved_by=1113930428. Two live-test bugs fixed: (1) CALLBACK_SECRET mismatch (API didn't load .env.local, bot had correct secret → all callbacks rejected) — fixed with .env symlink; (2) project.repo_path `/opt/agent-control/repos/agentrouter` invalid — fixed to `/root/agentrouter`. Validation baseline: API 275/275, Telegram-bot 79/79, Worker 98/98, ruff clean. No BUTTON_DATA_INVALID errors. Services: API stub (uvicorn :8000), Celery worker, Telegram bot — all in WSL with native PostgreSQL 14 + Redis.

- **INFRA-02 TG-06 Regression Live Smoke (studio-orchestrator):** Validated TG-06 compact callback flow with zero manual workarounds. Task-0002 approved via inline button, notification delivered (message_id=73), callback-answer 200, approve 200, 38-byte callback data, 370ms handling. No BUTTON_DATA_INVALID, TelegramBadRequest, CALLBACK_SECRET mismatch, Path-escapes, tracebacks, duplicates, feedback loop, token leakage. Zero manual workarounds: no temp `.env`, no manual `UPDATE repo_path`, CALLBACK_SECRET and repo_path loaded automatically. Verdict: PASS. INFRA-01 fixes confirmed working.

- **MEM-04 Phase 2 Soft Mandatory Memory Checkpoints (knowledge-steward):** Implemented soft enforcement of mandatory memory checkpoints. Phase 1 finding: 0/57 legacy task logs contained "Memory updated" phrase — audit gap documented but not backfilled. Phase 2 (docs-only): (1) AGENTS.md — rule #7 "Memory checkpoint — обязательное правило" with full mandatory rules, when required/skippable, closeout format, enforcement phases. (2) `.ai_memory/runbooks/memory-checkpoint.md` — NEW runbook (10 sections). (3) `.ai_memory/templates/task-summary-template.md` — enhanced "Память обновлена" checklist 3→7 items with mandatory note. (4) `docs/memory-system.md` — added memory checkpoint reference and link. Phase 3 API gate (`memory_checkpoint_done` flag) deferred. Enforcement: studio-orchestrator responsible for verifying checkpoints. Risk: low (docs-only, no code changes). 5 files changed (4 modified + 1 new runbook).

- **SEC-01 Phase 3 Live Smoke: PermissionEngine admin gate validation (security-engineer):** Validated PermissionEngine admin gate against real Telegram approval flows. 3 medium-risk tasks (54b895cf, bc665abf, cd0143a0) tested: inline approve via compact callback → 200 OK (task-0001), command /approve → 200 OK (task-0002), command /reject → 200 OK (task-0003). Zero 403 PERMISSION DENIED responses. All 3 admin-gated operations passed. User 1113930428 correctly authenticated by TELEGRAM_ADMIN_USER_IDS. No BUTTON_DATA_INVALID, no BadRequest, no signature errors, zero tracebacks. Compact callback protocol preserved. approved_by correctly set to 1113930428 on all operations. Reason correctly stored on reject. No security policy violations. Verdict: PASS. 0 files changed (memory-only).

- **SEC-02 Phase 2 Audit Model, Migration & Service (security-engineer):** Implemented infrastructure for security audit trail. Created `SecurityAuditEvent` SQLAlchemy model (21 columns, append-only). Alembic migration `0002_add_security_audit_events` (additive only, 5 indexes, 4 FK SET NULL). `SecurityAuditService` with 5 methods (record, record_best_effort, query_by_task, query_by_actor, query_by_decision). Redaction helpers (redact_text, sanitize_metadata, hash_ip). Registered in models/__init__.py. 34 new tests. Validation: API 331/331, Bot 79/79, Worker 98/98, Total 508/508, ruff clean. Migration validated via `alembic upgrade head --sql` only. No wiring into endpoints yet (Phase 3). 5 files changed (4 new + 1 modified).\n\n- **SEC-01 Phase 2 Permission Engine MVP (security-engineer):** Implemented centralized Permission Engine with fail-closed design and wired to 5 critical API endpoints. Created `apps/api/app/security/` package: `permissions.py` (PermissionEngine, 14 PermissionAction enum, PermissionDecision + PermissionContext Pydantic models), `context.py` (helper factories). Wired to: (1) `POST /approvals/{id}/approve` admin-gated, (2) `POST /approvals/{id}/reject` admin-gated, (3) `POST /tasks/{id}/trigger-plan` risk-level gating (low→allow, medium→allow+approval, high/critical→deny), (4) `POST /tasks/{id}/callback-answer` admin check, (5) `PATCH /tasks/{id}/status` system actor check. 8 stubbed actions (always allow), unknown actions always denied. Added `TELEGRAM_ADMIN_USER_IDS` to config. 19 new unit tests + 3 integration tests. Validation: API 297/297 ✅ (was 275), Telegram-bot 79/79 ✅, Worker 98/98 ✅. 10 files changed (4 new, 6 modified). No DB schema changes, no migrations, no secrets exposed.

- **INFRA-01 Dev Runtime Config Drift Fix (studio-orchestrator):** Permanent fixes for the two TG-06 Phase 3 live-test bugs. **Fix A:** `start-api-stub.sh` now sources `.env.local` process-scoped (same pattern as `start-worker.sh`), logs CALLBACK_SECRET status, and reports DATABASE_URL source. **Fix B:** New `bootstrap-seed.sh` ensures `agentrouter` project and `studio-orchestrator` agent exist in dev DB with platform-correct `repo_path=$(realpath "$PROJECT_ROOT")` (idempotent via INSERT ON CONFLICT). Both scripts support `--dry-run` and `--help`; no DROP/TRUNCATE/DELETE. Validation: bash -n 11/11, API/Worker/Telegram-bot pytest all pass, runtime smoke confirmed, temp .env absent, no secrets printed.

- **TG-04 Live Integration Phase 1 (security-engineer + backend-architect):** Security prerequisites IMPLEMENTED. `config.py`: TELEGRAM_ADMIN_USER_IDS (comma-separated, fail-closed parser). `handlers/messages.py`: is_bot guard (skip from_user.is_bot). `logging.py` (NEW): SecretRedactionFilter (redacts tokens, API keys, bearer, DB/Redis passwords). Tests: 5 admin ID parsing + 7 SecretRedactionFilter + 2 is_bot = 14 new tests. `docs/telegram-live-runbook.md` (NEW): env checklist, startup, abort criteria, safety gates. Validation: compileall clean, ruff clean, pytest 64/64 pass. No live bot started, no .env/secrets changed, no migrations/deploy, no OpenCode.

- **TG-04 HTML placeholder fix (studio-orchestrator):** Fixed `TelegramBadRequest: Unsupported start tag "project_slug"`. Bot has global `parse_mode=HTML`; raw `<project_slug>` in help text was parsed as HTML tag. Replaced raw placeholders with `<code>placeholder</code>` in 6 handler files. Added `html.escape()` for dynamic API/user values in 4 handlers. Fixed import order for ruff I001. Updated 1 test assertion. Validation: compileall ✅, ruff ✅, pytest 64/64 ✅. No secrets touched, .env.local gitignored.

- **TG-04 private chat wording fix (studio-orchestrator):** In private chat, "Этот topic" replaced with "Этот чат" via `message.chat.type == "private"` check. Added `test_text_message_unbound_private_chat`. Validation: compileall ✅, ruff ✅, pytest 65/65 ✅. No secrets touched.

- **TG-04 private chat binding support (studio-orchestrator):** `/bind_topic`, `/unbind_topic`, `/topic_status` now work in private chats. Private chat uses `message_thread_id=0` as sentinel (DB NOT NULL BigInteger). Removed forum-only guards from 3 handlers. Added `chat_type` to `FakeMessage`. 3 new tests: `test_bind_topic_private_chat`, `test_unbind_topic_private_chat`, `test_topic_status_private_chat_unbound`. Validation: compileall ✅, ruff ✅, pytest 67/67 ✅. No secrets touched, no migrations needed.

- **DEV-LINUX-01 Ubuntu 22.04 runtime scripts (studio-orchestrator):** Created 10 bash scripts in `scripts/dev-linux/` replacing Windows PS1 automation. All scripts: `set -euo pipefail`, `--dry-run`, `--help`. Process management: `nohup` + PID files in `.runtime/`. Services: API stub, API opencode_http, OpenCode server, Celery worker, Telegram bot. Tests: stub smoke, real OpenCode smoke. Infrastructure: check-db, bootstrap-db, cleanup. Safety: 127.0.0.1 only, PID validation, cleanup never touches DB/containers. Docs: `docs/dev-linux-runbook.md`. .gitignore: added `.runtime/`. Windows PS1 scripts preserved as legacy. No Python code changes, no docker-compose changes, no .env changes.

- **DEV-LINUX-01B dry-run precondition fix (studio-orchestrator):** Fixed 5 scripts where preconditions (curl, redis-cli, docker exec, API/OpenCode health checks) executed BEFORE `if $DRY_RUN` branch. 2 scripts exited 1 in dry-run, 3 made real network connections. Fix: wrapped all preconditions in `if ! $DRY_RUN` guards. Scripts: start-api-opencode.sh, smoke-real-opencode-runtime.sh, start-worker.sh, start-telegram-bot.sh, smoke-stub-runtime.sh. Validation: bash -n 10/10, --help 10/10, --dry-run 10/10 (all exit 0), no real connections, no processes, no artifacts.

- **DEV-LINUX-01C real stub contour validation (studio-orchestrator):** Full stub contour validated on WSL Ubuntu 22.04. Three blockers fixed: (1) venv auto-detection added to 8 scripts, (2) JSON shell interpolation replaced with temp files in smoke scripts, (3) events URL corrected. Real contour: check-db ✅, start-api-stub ✅, start-worker ✅, smoke-stub-runtime ✅ (ALL 8 CHECKS PASS), cleanup-runtime ✅. No secrets, no .env, no code changes.

- **DEV-LINUX-01D real OpenCode runtime contour (studio-orchestrator):** Full real OpenCode contour validated on WSL Ubuntu 22.04. Environment: Ubuntu 22.04.5 LTS, Node v20.20.2, npm 10.8.2, OpenCode 1.14.39. Results: check-db ✅ (9/9 tables, alembic head), start-opencode ✅ (PID 8570, 127.0.0.1:4096, /global/health 200), CLI attach probe ✅ (~42s, session ses_201ad1cf9ffeuGz8Ag5JiGQM0v), start-api-opencode ✅ (PID 9014, 127.0.0.1:8000, provider opencode_http), smoke-real-opencode-runtime ✅ (task bc4853b6, approved, 103.2s, session ses_201a17dfcffem78R3kuE96eZPf, 2099 chars plan), cleanup ✅. Event timeline: task_created → runtime_session_created → runtime_retry_scheduled → runtime_event_received ×2 → plan_generated. All 9 validation checks PASS. Findings: (1) first smoke hit 420s timeout on cold-start; (2) smoke script missing normalized_text field; (3) Node.js missing in WSL; (4) OpenCode npm is platform-specific. No secrets, no .env, no code changes.

- **WORKER-LINUX-01 Celery SIGHUP restart crash fix (studio-orchestrator):** Fixed Celery worker dying after every task. Root cause: Celery 5.6.3 installs SIGHUP restart handler for non-TTY stdout (nohup). On shell exit, SIGHUP triggers `os.execv(sys.executable, [sys.executable] + sys.argv)` which runs `celery/__main__.py` as standalone script (not via `-m`), breaking relative imports. Fix: (1) monkey-patch `_reload_current_worker` in celery_app.py to use `python -m celery`, (2) SIGHUP→SIG_IGN via `@worker_ready.connect`, (3) `disown` in start-worker.sh. Changed files: `apps/worker/app/celery_app.py` (+44 lines), `scripts/dev-linux/start-worker.sh` (+6 lines). Validation: task-0009 approved, worker alive after 35s, 0 ImportError/Traceback, 93 worker tests PASS, cleanup PASS, git commit 4eb0fd2.

- **TG-04 Phase 5 Live Private Chat E2E (studio-orchestrator):** Full live Telegram private chat E2E validated. Components: API stub (PID 12328), Celery worker (PID 13000, SIGHUP fix active), Telegram bot @agentrouters_bot (PID 13087). User sent "TG-04 final live smoke" in private chat. Bot received → created task-0010 (5d16fe1e) → triggered plan → worker picked up → runtime plan → approved → notification dispatched (StubNotifier). Processing: 0.125s worker + 1.49s bot handler. 11/11 validation checks PASS: task_created, plan_triggered, runtime_session_created (stub-session), plan_generated=1, status=approved, no runtime_error, no policy_blocked, notification dispatched, worker alive, bot alive, no feedback loop (10 tasks total, 0 after task-0010). Observations: TelegramConflictError transient conflicts (recovered), StubNotifier used (worker env lacks token), no runtime_session_created event in task_events (in payload). Cleanup: all processes stopped, API restarted stub, ports clean.

## VPS Server State (45.130.213.12)

| Component | Status |
|-----------|--------|
| OS | Ubuntu 24.04.4 LTS, kernel 6.8.0-106-generic, systemd v255 |
| CPU | 2 vCPU |
| RAM | 3.8 GiB |
| Disk | 40 GB (36 GB free) |
| Swap | 2.0 GiB configured, 0 B used |
| Docker Engine | 29.4.3 active |
| Docker Compose | v5.1.3 |
| User agentmc | UID 999, docker group |
| /opt/agent-control | agentmc:agentmc 750 ✅ |
| /var/log/agentrouter | agentmc:agentmc 750 ✅ |
| /var/lib/agentrouter | agentmc:agentmc 750 ✅ |
| UFW | active, SSH (22/tcp) only |
| HTTP/HTTPS | NOT opened (no domain) |
| Repo cloned | ✅ YES (`/opt/agent-control/agentrouter`) |
| .env created | ✅ YES (mode 600, owner agentmc; values hidden) |
| App deployed | ❌ NO |

## Следующие шаги

1. Real production deploy (requires explicit approval)
2. PR automation (GitHub/GitLab integration)
3. Frontend dashboard (React + Vite + shadcn/ui)
4. Memory retrieval tuning: ranking quality + scope heuristics
5. Full backlog: [../docs/mvp-backlog.md](../docs/mvp-backlog.md)

## Кодовая база (новое)

| Компонент | Статус | Файлы |
|-----------|--------|-------|
| FastAPI app | ✅ | `apps/api/app/main.py` |
| /health endpoint | ✅ | `apps/api/app/routers/health.py` (enhanced: DB + Redis checks) |
| Settings (pydantic) | ✅ | `apps/api/app/config.py` |
| pyproject.toml | ✅ | `apps/api/pyproject.toml` |
| SQLAlchemy models | ✅ | `apps/api/app/models/*.py` |
| Alembic | ✅ | `apps/api/alembic/*` |
| Dev docker-compose | ✅ | `infra/docker/docker-compose.yml` |
| Telegram bot gateway | ✅ | `apps/telegram-bot/app/*` |
| Runtime adapter (plan-only) | ✅ | `apps/api/app/integrations/opencode/*`, `apps/api/app/services/runtime_service.py`, `apps/api/app/routers/runtime.py` |
| Celery worker skeleton | ✅ | `apps/worker/app/*` (celery_app, config, queues, 7 task modules) |
| Memory provisioning | ✅ | `apps/api/app/services/memory_provisioning_service.py`, `apps/api/app/schemas/memory.py` |
| Memory CRUD API | ✅ | `apps/api/app/routers/memory.py`, `apps/api/app/services/memory_policy_service.py`, `apps/api/app/services/memory_service.py` |
| Memory indexing + retrieval | ✅ | `apps/api/app/services/memory_{chunking,embedding,indexing,retrieval}_service.py`, `POST /memory/reindex`, `POST /memory/search` |
| Sandbox infra (WRK-03 prep) | ✅ | `infra/docker/Dockerfile.{api,telegram-bot,worker,sandbox}`, `infra/docker/sandbox.compose.yml` |
| Safe execute pipeline | ✅ | `apps/worker/app/tasks/agent_execute.py`, `apps/worker/app/services/{command_policy,worktree_policy,redaction,sandbox_runner}.py` |
| Production deploy templates | ✅ | `infra/deploy/{Caddyfile,*.service,README.md}`, `infra/docker/docker-compose.prod.yml`, `.env.example`, `scripts/deploy/validate-production-templates.sh` |

## Memory vault статус

| Компонент | Статус |
|-----------|--------|
| Правила | ✅ |
| Навигация | ✅ |
| Шаблоны (5) | ✅ |
| ADR (4) | ✅ |
| **Task logs** | 89 |
| Проекты | 0 |
