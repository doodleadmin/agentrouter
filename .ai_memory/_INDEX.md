# _INDEX.md — Навигация по vault

> Автоматический индекс. Обновляется при provisioning и после задач.

---

## Структура

| Раздел | Путь | Описание |
|--------|------|----------|
| Правила | [README.md](README.md) | Правила vault |
| Глобальный статус | [current_state.md](current_state.md) | Текущий статус системы |
| Пайплайн | [agent_mission_control_pipeline.md](agent_mission_control_pipeline.md) | Полный маршрут реализации |
| Проекты | [projects/](projects/) | Память по проектам |
| Агенты | [agents/](agents/) | Профили агентов |
| Задачи | [tasks/](tasks/) | Логи задач |
| Решения | [decisions/](decisions/) | Архитектурные решения (ADR) |
| Шаблоны | [templates/](templates/) | Шаблоны документов |

---

## Счётчики

| Категория | Количество |
|-----------|-----------|
| **Проекты** | 0 |
| **Агенты (профили)** | 0 |
| **ADR** | 4 |
| **Task logs** | 99 |
| **Шаблоны** | 5 |

---

## Зарегистрированные проекты

*Пока нет зарегистрированных проектов.*

---

## Агенты

| Агент | Профиль памяти |
|-------|---------------|
| backend-architect | — |
| frontend-developer | — |
| devops-automator | — |
| explore | — |
| knowledge-steward | — |
| security-engineer | — |
| git-workflow-master | — |
| reality-checker | — |
| studio-orchestrator | — |

---

## ADR

| ID | Название | Файл |
|----|----------|------|
| 0001 | Use Monorepo | [0001-use-monorepo.md](decisions/0001-use-monorepo.md) |
| 0002 | Python Backend (FastAPI) | [0002-python-backend-fastapi.md](decisions/0002-python-backend-fastapi.md) |
| 0003 | pgvector for Retrieval | [0003-pgvector-for-retrieval.md](decisions/0003-pgvector-for-retrieval.md) |
| 0004 | Celery + Redis for Queues | [0004-celery-redis-for-queues.md](decisions/0004-celery-redis-for-queues.md) |

---

## Task Logs

| Файл | Задача |
|------|--------|
| [2026-05-03-task-fnd01-fnd02.md](tasks/2026-05-03-task-fnd01-fnd02.md) | FND-01 + FND-02 |
| [2026-05-09-task-vps03a-ssh-swap-repo-bootstrap.md](tasks/2026-05-09-task-vps03a-ssh-swap-repo-bootstrap.md) | VPS-03A |
| [2026-05-03-task-fnd03-db-foundation.md](tasks/2026-05-03-task-fnd03-db-foundation.md) | FND-03 |
| [2026-05-03-task-fnd03-fix.md](tasks/2026-05-03-task-fnd03-fix.md) | FND-03 fix |
| [2026-05-03-task-dop01-dev-docker-compose.md](tasks/2026-05-03-task-dop01-dev-docker-compose.md) | DOP-01 |
| [2026-05-03-task-dop01-safe-local-check.md](tasks/2026-05-03-task-dop01-safe-local-check.md) | DOP-01 safe local check |
| [2026-05-03-task-be01-crud.md](tasks/2026-05-03-task-be01-crud.md) | BE-01 |
| [2026-05-03-task-be02-approvals.md](tasks/2026-05-03-task-be02-approvals.md) | BE-02 |
| [2026-05-03-task-tg01-telegram-gateway.md](tasks/2026-05-03-task-tg01-telegram-gateway.md) | TG-01 |
| [2026-05-03-task-tg02-topic-binding-routing.md](tasks/2026-05-03-task-tg02-topic-binding-routing.md) | TG-02 |
| [2026-05-03-task-be03-runtime-plan-only.md](tasks/2026-05-03-task-be03-runtime-plan-only.md) | BE-03 |
| [2026-05-03-task-wrk01-celery-worker.md](tasks/2026-05-03-task-wrk01-celery-worker.md) | WRK-01 |
| [2026-05-03-task-wrk02-plan-pipeline.md](tasks/2026-05-03-task-wrk02-plan-pipeline.md) | WRK-02 |
| [2026-05-03-task-mem01-memory-provisioning.md](tasks/2026-05-03-task-mem01-memory-provisioning.md) | MEM-01 |
| [2026-05-03-task-mem02-memory-crud-api.md](tasks/2026-05-03-task-mem02-memory-crud-api.md) | MEM-02 |
| [2026-05-03-task-mem03-memory-indexing-retrieval.md](tasks/2026-05-03-task-mem03-memory-indexing-retrieval.md) | MEM-03 |
| [2026-05-03-task-dop02-dockerfiles-sandbox-compose.md](tasks/2026-05-03-task-dop02-dockerfiles-sandbox-compose.md) | DOP-02 |
| [2026-05-03-task-security-review-before-wrk03.md](tasks/2026-05-03-task-security-review-before-wrk03.md) | Security review before WRK-03 |
| [2026-05-03-task-wrk03-safe-execute-pipeline.md](tasks/2026-05-03-task-wrk03-safe-execute-pipeline.md) | WRK-03 |
| [2026-05-03-task-wrk03-hardening.md](tasks/2026-05-03-task-wrk03-hardening.md) | WRK-03 hardening |
| [2026-05-03-task-wrk03-fake-e2e.md](tasks/2026-05-03-task-wrk03-fake-e2e.md) | WRK-03 fake E2E |
| [2026-05-03-task-wrk04-docker-sandbox-runner.md](tasks/2026-05-03-task-wrk04-docker-sandbox-runner.md) | WRK-04 |
| [2026-05-03-task-wrk04-polish-pre-manual-test.md](tasks/2026-05-03-task-wrk04-polish-pre-manual-test.md) | WRK-04 polish |
| [2026-05-03-task-wrk04-manual-local-test.md](tasks/2026-05-03-task-wrk04-manual-local-test.md) | WRK-04 manual local test |
| [2026-05-03-task-wrk04-real-docker-smoke-test.md](tasks/2026-05-03-task-wrk04-real-docker-smoke-test.md) | WRK-04 real docker smoke test |
| [2026-05-04-task-wrk04-manual-test-hardening.md](tasks/2026-05-04-task-wrk04-manual-test-hardening.md) | WRK-04 manual-test hardening |
| [2026-05-04-task-be04-runtime-guardrails.md](tasks/2026-05-04-task-be04-runtime-guardrails.md) | BE-04 runtime guardrails |
| [2026-05-04-task-be04-review-blockers-fix.md](tasks/2026-05-04-task-be04-review-blockers-fix.md) | BE-04 review blockers fix |
| [2026-05-04-task-be04-transport-hardening.md](tasks/2026-05-04-task-be04-transport-hardening.md) | BE-04 transport hardening |
| [2026-05-04-task-be05-transport-gap-closures.md](tasks/2026-05-04-task-be05-transport-gap-closures.md) | BE-05 RealOpenCodeHttpTransport + gaps |
| [2026-05-04-task-be05-hardening-b1-m1-m2-m3.md](tasks/2026-05-04-task-be05-hardening-b1-m1-m2-m3.md) | BE-05 hardening (B-1 + M-1/M-2/M-3) |
| [2026-05-04-task-be05-hardening-phase1.md](tasks/2026-05-04-task-be05-hardening-phase1.md) | BE-05 Phase 1 hardening (B-1+M-1/M-2/M-3) |
| [2026-05-04-devops-opencode-smoke-test-plan.md](tasks/2026-05-04-devops-opencode-smoke-test-plan.md) | DevOps OpenCode smoke test plan |
| [2026-05-04-task-be06-controlled-smoke-test-plan.md](tasks/2026-05-04-task-be06-controlled-smoke-test-plan.md) | BE-06 controlled OpenCode smoke test plan/preflight |
| [2026-05-04-task-be06-smoke-docs-fix.md](tasks/2026-05-04-task-be06-smoke-docs-fix.md) | BE-06 smoke docs fix (no .env edits) |
| [2026-05-04-task-be06-rerun-plan-after-step-b-abort.md](tasks/2026-05-04-task-be06-rerun-plan-after-step-b-abort.md) | BE-06 rerun plan after Step-B abort |
| [2026-05-04-task-be06-transport-compatibility-fix.md](tasks/2026-05-04-task-be06-transport-compatibility-fix.md) | BE-06 transport compatibility fix (/session + /message) |
| [2026-05-04-task-be06-task-creation-fix.md](tasks/2026-05-04-task-be06-task-creation-fix.md) | BE-06 task creation fix (transaction boundary + FK mapping) |
| [2026-05-04-task-be06-final-execution.md](tasks/2026-05-04-task-be06-final-execution.md) | BE-06 FINAL EXECUTION (real OpenCode smoke test) |
| [2026-05-04-task-be07-payload-contract-alignment-implementation.md](tasks/2026-05-04-task-be07-payload-contract-alignment-implementation.md) | BE-07 implementation: OpenCode payload contract alignment |
| [2026-05-04-task-be07-plus-implementation.md](tasks/2026-05-04-task-be07-plus-implementation.md) | BE-07+ implementation: OpenCode 1.14.33 native contract alignment |
| [2026-05-04-task-dev-db-01-alembic-async-fix.md](tasks/2026-05-04-task-dev-db-01.md) | DEV-DB-01: Fix Alembic async/sync engine mismatch |
| [2026-05-04-task-be08-session-traceability-timeout.md](tasks/2026-05-04-task-be08-session-traceability-timeout.md) | BE-08: OpenCode session traceability + timeout tuning |
| [2026-05-04-task-be08-real-opencode-smoke-success.md](tasks/2026-05-04-task-be08-real-opencode-smoke-success.md) | BE-08-real: OpenCode smoke SUCCESS (first real plan_generated) |
| [2026-05-04-task-be09-phase1-worker-timeout.md](tasks/2026-05-04-task-be09-phase1-worker-timeout.md) | BE-09 Phase 1: Worker API_TIMEOUT_SECONDS 30→300 fix |
| [2026-05-04-task-be09-phase2-real-opencode-e2e-success.md](tasks/2026-05-04-task-be09-phase2-real-opencode-e2e-success.md) | BE-09 Phase 2: Real OpenCode E2E — SUCCESS |
| [2026-05-04-task-be10-runtime-reliability-hardening.md](tasks/2026-05-04-task-be10-runtime-reliability-hardening.md) | BE-10: Runtime Reliability Hardening (6 hardening items) |
| [2026-05-04-task-be10-real-opencode-regression-smoke.md](tasks/2026-05-04-task-be10-real-opencode-regression-smoke.md) | BE-10: Real OpenCode Regression Smoke — PASSED |
| [2026-05-04-task-be11-runtime-runbook-automation.md](tasks/2026-05-04-task-be11-runtime-runbook-automation.md) | BE-11: Runtime Runbook + Local Smoke Automation Scripts |
| [2026-05-05-task-be12-opencode-read-timeout-alignment.md](tasks/2026-05-05-task-be12-opencode-read-timeout-alignment.md) | BE-12: OpenCode Read-Timeout Alignment |
| [2026-05-05-task-be11-scripts-final-repair.md](tasks/2026-05-05-task-be11-scripts-final-repair.md) | BE-11: Scripts Final Repair (parse/dry-run PASS) |
| [2026-05-06-task-dev-linux-01-runtime-scripts.md](tasks/2026-05-06-task-dev-linux-01-runtime-scripts.md) | DEV-LINUX-01: Ubuntu 22.04 Runtime Scripts |
| [2026-05-06-task-dev-linux-01b-dryrun-fix.md](tasks/2026-05-06-task-dev-linux-01b-dryrun-fix.md) | DEV-LINUX-01B: Dry-Run Precondition Fix |
| [2026-05-06-task-dev-linux-01c-real-stub-contour.md](tasks/2026-05-06-task-dev-linux-01c-real-stub-contour.md) | DEV-LINUX-01C: Real Stub Contour Validation |
| [2026-05-06-task-dev-linux-01d-real-opencode-contour.md](tasks/2026-05-06-task-dev-linux-01d-real-opencode-contour.md) | DEV-LINUX-01D: Real OpenCode Runtime Contour |
| [2026-05-06-task-tg03-telegram-approvals-ux.md](tasks/2026-05-06-task-tg03-telegram-approvals-ux.md) | TG-03: Telegram Approvals + Task Status UX |
| [2026-05-06-task-tg04-live-integration-phase1.md](tasks/2026-05-06-task-tg04-live-integration-phase1.md) | TG-04 Phase 1: Live Integration Security Prereqs |
| [2026-05-06-task-tg04-aiogram-message-thread-fix.md](tasks/2026-05-06-task-tg04-aiogram-message-thread-fix.md) | TG-04: aiogram 3.15 message_thread_id compatibility fix |
| [2026-05-06-task-tg04-html-placeholder-fix.md](tasks/2026-05-06-task-tg04-html-placeholder-fix.md) | TG-04: HTML placeholder fix (TelegramBadRequest) |
| [2026-05-06-task-tg04-private-chat-wording-fix.md](tasks/2026-05-06-task-tg04-private-chat-wording-fix.md) | TG-04: Private chat wording fix |
| [2026-05-06-task-tg04-private-chat-binding-support.md](tasks/2026-05-06-task-tg04-private-chat-binding-support.md) | TG-04: Private chat binding support |
| [2026-05-06-task-tg-04-phase5-live-e2e.md](tasks/2026-05-06-task-tg-04-phase5-live-e2e.md) | TG-04 Phase 5: Live Private Chat E2E |
| [2026-05-06-task-tg05-live-notifications-admin-gate.md](tasks/2026-05-06-task-tg05-live-notifications-admin-gate.md) | TG-05 Phase 1: Live Notifications + Admin Gate |
| [2026-05-06-task-worker-linux-01-celery-sighup-fix.md](tasks/2026-05-06-task-worker-linux-01-celery-sighup-fix.md) | WORKER-LINUX-01: Celery SIGHUP Restart Fix |
| [2026-05-07-task-tg06-phase2-compact-callbacks.md](tasks/2026-05-07-task-tg06-phase2-compact-callbacks.md) | TG-06 Phase 2: Compact Telegram Callback Protocol |
| [2026-05-07-task-tg06-phase3-live-test.md](tasks/2026-05-07-task-tg06-phase3-live-test.md) | TG-06 Phase 3: Live Compact Callback E2E |
| [2026-05-07-task-tg05-phase2-live-notification-smoke.md](tasks/2026-05-07-task-tg05-phase2-live-notification-smoke.md) | TG-05 Phase 2: Live Notification Smoke |
| [2026-05-07-task-tg05-phase3-admin-approval-flow.md](tasks/2026-05-07-task-tg05-phase3-admin-approval-flow.md) | TG-05 Phase 3: Admin Approval Flow |
| [2026-05-07-task-tg05-phase4-admin-reject-flow.md](tasks/2026-05-07-task-tg05-phase4-admin-reject-flow.md) | TG-05 Phase 4: Admin Reject Flow |
| [2026-05-07-task-tg05-closeout.md](tasks/2026-05-07-task-tg05-closeout.md) | TG-05: Closeout |
| [2026-05-07-task-ci-01-phase1-local-validation.md](tasks/2026-05-07-task-ci-01-phase1-local-validation.md) | CI-01 Phase 1: Local Validation Pipeline |
| [2026-05-07-task-ci-02-local-validation-fixes.md](tasks/2026-05-07-task-ci-02-local-validation-fixes.md) | CI-02: Local Validation Fixes |
| [2026-05-07-task-infra-01-dev-runtime-config.md](tasks/2026-05-07-task-infra-01-dev-runtime-config.md) | INFRA-01: Dev Runtime Config Drift Fix |
| [2026-05-07-task-infra-02-tg06-regression-live-smoke.md](tasks/2026-05-07-task-infra-02-tg06-regression-live-smoke.md) | INFRA-02: TG-06 Regression Live Smoke |
| [2026-05-07-task-mem04-memory-checkpoints.md](tasks/2026-05-07-task-mem04-memory-checkpoints.md) | MEM-04 Phase 2: Soft Mandatory Memory Checkpoints |
| [2026-05-07-task-sec01-permission-engine.md](tasks/2026-05-07-task-sec01-permission-engine.md) | SEC-01 Phase 2: Permission Engine MVP |
| [2026-05-08-task-sec01-phase3-live-smoke.md](tasks/2026-05-08-task-sec01-phase3-live-smoke.md) | SEC-01 Phase 3: Live Smoke — Admin Gate Validation |
| [2026-05-08-task-sec02-phase2-audit-model-service.md](tasks/2026-05-08-task-sec02-phase2-audit-model-service.md) | SEC-02 Phase 2: Security Audit DB Model, Migration & Service |
| [2026-05-08-task-sec02-phase3-audit-integration.md](tasks/2026-05-08-task-sec02-phase3-audit-integration.md) | SEC-02 Phase 3: Integrate P0 Security Audit Points |
| [2026-05-08-task-sec02-phase4-live-smoke.md](tasks/2026-05-08-task-sec02-phase4-live-smoke.md) | SEC-02 Phase 4: Live Smoke — Audit Trail Validation |
| [2026-05-08-task-sec03-secrets-redaction.md](tasks/2026-05-08-task-sec03-secrets-redaction.md) | SEC-03 Phase 2: Centralized Secrets Redaction |
| [2026-05-08-task-sec03-phase3-live-redaction-smoke.md](tasks/2026-05-08-task-sec03-phase3-live-redaction-smoke.md) | SEC-03 Phase 3: Live Redaction Smoke |
| [2026-05-08-task-sec03b-sqlalchemy-log-safety.md](tasks/2026-05-08-task-sec03b-sqlalchemy-log-safety.md) | SEC-03B Phase 2: SQLAlchemy Log Safety |
| [2026-05-08-task-dop03-production-runtime-templates.md](tasks/2026-05-08-task-dop03-production-runtime-templates.md) | DOP-03 Phase 2: Production Runtime Templates + Enhanced Health Check |
| [2026-05-08-task-dop03-phase3-dry-run-validation.md](tasks/2026-05-08-task-dop03-phase3-dry-run-validation.md) | DOP-03 Phase 3: Production Templates Dry-run Validation |
| [2026-05-08-task-dop04-release-workflow.md](tasks/2026-05-08-task-dop04-release-workflow.md) | DOP-04 Phase 2: Safe Release/Rollback Workflow Artifacts + Memory Checkpoint |
| [2026-05-08-task-dop04-phase3-dry-run-release-validation.md](tasks/2026-05-08-task-dop04-phase3-dry-run-release-validation.md) | DOP-04 Phase 3: Release Workflow Dry-run Validation |
| [2026-05-09-task-backlog02-mvp-backlog-audit.md](tasks/2026-05-09-task-backlog02-mvp-backlog-audit.md) | BACKLOG-02: MVP Backlog Completion Audit + Roadmap Sync |
| [2026-05-09-task-readme-github-polish.md](tasks/2026-05-09-task-readme-github-polish.md) | README-01: GitHub README Polish |
| [2026-05-09-task-vps01-server-preflight.md](tasks/2026-05-09-task-vps01-server-preflight.md) | VPS-01: Server Preflight Inspection |
| [2026-05-09-task-vps02-base-server-setup.md](tasks/2026-05-09-task-vps02-base-server-setup.md) | VPS-02: Base Server Setup (45.130.213.12) |
| [2026-05-09-task-vps03b-env-db-redis-bootstrap.md](tasks/2026-05-09-task-vps03b-env-db-redis-bootstrap.md) | VPS-03B: .env + DB/Redis bootstrap only (45.130.213.12) |
| [2026-05-09-task-vps03c-telegram-secrets-preflight.md](tasks/2026-05-09-task-vps03c-telegram-secrets-preflight.md) | VPS-03C: Telegram secrets verification + preflight dry-run |
| [2026-05-09-task-vps04-controlled-migration-app-start.md](tasks/2026-05-09-task-vps04-controlled-migration-app-start.md) | VPS-04: Controlled Migration + App Start |
| [2026-05-09-task-vps05a-polling-runtime-smoke.md](tasks/2026-05-09-task-vps05a-polling-runtime-smoke.md) | VPS-05A: Polling Runtime Smoke |
| [2026-05-09-task-vps05b-domain-caddy-https.md](tasks/2026-05-09-task-vps05b-domain-caddy-https.md) | VPS-05B: Domain + Caddy + HTTPS Verification |
| [2026-05-09-task-vps06c-offsite-s3-sync.md](tasks/2026-05-09-task-vps06c-offsite-s3-sync.md) | VPS-06C: Offsite Backup Sync to Beget S3 |
| [2026-05-09-task-vps07b-healthchecks-ping.md](tasks/2026-05-09-task-vps07b-healthchecks-ping.md) | VPS-07B: Healthchecks.io Ping Integration |
| [2026-05-09-task-vps06b-logrotate-backup-verify.md](tasks/2026-05-09-task-vps06b-logrotate-backup-verify.md) | VPS-06B: Log Rotation + Backup Verification |
| [2026-05-09-task-vps06a-backups-health-monitoring.md](tasks/2026-05-09-task-vps06a-backups-health-monitoring.md) | VPS-06A: Backups + Health Monitoring Baseline |

---

## Шаблоны

| Шаблон | Файл |
|--------|------|
| Project Memory (7 файлов) | [project-memory-template.md](templates/project-memory-template.md) |
| Task Summary | [task-summary-template.md](templates/task-summary-template.md) |
| Agent Notes | [agent-notes-template.md](templates/agent-notes-template.md) |
| ADR | [adr-template.md](templates/adr-template.md) |
| Current State | [current-state-template.md](templates/current-state-template.md) |
