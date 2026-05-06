# current_state.md — Текущий активный статус

Обновлено: 2026-05-07 | Автор: studio-orchestrator

---

## Статус проекта

**Фаза:** Phase 1 — Telegram Routing (TG-05 Notifications + Admin Gate in progress)
**Состояние:** FND-01..03, DOP-01, BE-01, BE-02, TG-01, TG-02, BE-03, WRK-01, WRK-02, MEM-01..03, DOP-02, WRK-03, WRK-03-hardening, WRK-03-fake-e2e, WRK-04, WRK-04-polish, WRK-04-manual-local-test, WRK-04-real-docker-smoke-test, WRK-04-manual-test-hardening, BE-04-review-fixes, BE-04-transport-hardening, BE-05-transport-gap-closures, BE-05-hardening-phase1, BE-06-task-creation-fix, BE-06-final-execution, BE-07-payload-contract-alignment, BE-07-plus-native-contract-alignment, DEV-DB-01-alembic-async-fix, BE-08-session-traceability-timeout, BE-08-real-opencode-smoke-success, BE-09-phase1-worker-timeout, BE-09-phase2-real-opencode-e2e-success, BE-10-runtime-reliability-hardening, BE-10-real-opencode-regression-smoke, BE-11-runtime-runbook-automation, BE-11-scripts-final-repair, BE-12-opencode-read-timeout-alignment, TG-03-telegram-approvals-ux, TG-04-live-integration-phase1, TG-04-aiogram-message-thread-fix, TG-04-html-placeholder-fix, TG-04-private-chat-wording-fix, TG-04-private-chat-binding-support, DEV-LINUX-01-ubuntu-runtime-scripts, DEV-LINUX-01b-dryrun-fix, DEV-LINUX-01c-real-stub-contour, DEV-LINUX-01d-real-opencode-contour, WORKER-LINUX-01-celery-sighup-fix, TG-04-phase5-live-private-chat-e2e, TG-05-phase1-notifications-admin-gate выполнены. CRITICAL/HIGH закрыты.
**Блокеры:** Нет (BE-04 security+architecture review blockers закрыты)
**Критические проблемы:** Нет

## Что происходит сейчас

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

- **BE-12 OpenCode read-timeout alignment (backend-architect):** `send_message()` локальный `httpx.AsyncClient` с `read=None` (SDK-aligned). `create_session()` bounded. Error mapping сохранён. Guardrails нетронуты. 16/16 transport tests pass (+5 BE-12). 251/252 full suite pass. Real OpenCode не запускался.
- **TG-03 Telegram Approvals + Task Status UX (backend-architect):** 7 phases complete. API: 409 for already-decided (was 422), GET /tasks/{id}/plan, POST /tasks/{id}/callback-answer with HMAC-signed callback validation. Bot: /status, /plan, /approve, /reject commands + inline keyboards (approve/reject/show-plan/refresh) + callback handler with API-side validation. API client extended (8 new methods). Formatters (task cards, approval cards, plan excerpts). Tests: 35/35 bot tests + 11 API tests pass (1 pre-existing flake).

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

## Следующие шаги

1. Memory retrieval tuning: ranking quality + scope heuristics
2. Полный план: [../docs/mvp-backlog.md](../docs/mvp-backlog.md)

## Кодовая база (новое)

| Компонент | Статус | Файлы |
|-----------|--------|-------|
| FastAPI app | ✅ | `apps/api/app/main.py` |
| /health endpoint | ✅ | `apps/api/app/routers/health.py` |
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

## Memory vault статус

| Компонент | Статус |
|-----------|--------|
| Правила | ✅ |
| Навигация | ✅ |
| Шаблоны (5) | ✅ |
| ADR (4) | ✅ |
| Логи задач | 53 (fnd-01-02, fnd-03, fnd-03-fix, dop-01, dop-01-check, be-01, be-02, tg-01, tg-02, be-03, wrk-01, wrk-02, mem-01, mem-02, mem-03, dop-02, security-review-before-wrk03, wrk-03, wrk-03-hardening, wrk-03-fake-e2e, wrk-04, wrk-04-polish, wrk-04-manual-local-test, wrk-04-real-docker-smoke-test, wrk-04-manual-test-hardening, be04-runtime-guardrails, be04-review-blockers-fix, be04-transport-hardening, be05-transport-gap-closures, be05-hardening-b1-m1-m2-m3, be06-controlled-smoke-test-plan, be06-smoke-docs-fix, be06-rerun-plan-after-step-b-abort, be06-transport-compatibility-fix, be06-task-creation-fix, be06-final-execution, be07-payload-contract-alignment-implementation, be07-plus-native-contract-alignment, be08-session-traceability-timeout, be08-real-opencode-smoke-success, dev-db-01-alembic-async-fix, be09-phase1-worker-timeout, be09-phase2-real-opencode-e2e-success, be10-runtime-reliability-hardening, be10-real-opencode-regression-smoke, be11-runtime-runbook-automation, be12-opencode-read-timeout-alignment, be11-scripts-final-repair, tg03-telegram-approvals-ux, tg04-live-integration-phase1, dev-linux-01-ubuntu-runtime-scripts, dev-linux-01b-dryrun-fix, dev-linux-01c-real-stub-contour, dev-linux-01d-real-opencode-contour) |
| Проекты | 0 |
