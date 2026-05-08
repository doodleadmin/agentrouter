# Roadmap — Agent Mission Control

Версия: 2.0
Дата: 2026-05-09
Обновлено: BACKLOG-02 Phase 2 (MVP audit + docs sync)

## Обзор

Разработка ведётся по 8 фазам, от инфраструктуры до web dashboard. Каждая фаза — это один спринт (1-2 недели).

```
Phase 0: Инфраструктура       ████████████████████  COMPLETE
Phase 1: Telegram routing      ████████████████████  COMPLETE
Phase 2: Project memory        ████████████████████  COMPLETE
Phase 3: OpenCode runtime      ████████████████████  COMPLETE
Phase 4: Safe execution        ████████████████████  COMPLETE
Phase 5: PR workflow           ░░░░░░░░░░░░░░░░░░░░  NOT STARTED / DEFERRED
Phase 6: DevOps/deploy         ████████████░░░░░░░░  DRY-RUN VALIDATED
Phase 7: Security/approval     ██████████████████░░  DRY-RUN VALIDATED
Phase 8: Web dashboard         ░░░░░░░░░░░░░░░░░░░░  NOT STARTED / v2
```

---

## Current real status as of BACKLOG-02 (2026-05-09)

**MVP v1 original backlog: 23/23 COMPLETE**

- Test baseline: API 401/401, Bot 79/79, Worker 98/98 — **Total 578/578 PASS**
- Security chain: SEC-01 Permission Engine, SEC-02 Audit Trail, SEC-03 Secrets Redaction, SEC-03B SQLAlchemy Log Safety — all PASS
- Deploy templates: DOP-03 production runtime templates — **dry-run validated**
- Release workflow: DOP-04 safe release/rollback scripts — **dry-run validated**
- **Real production deploy has NOT been executed**
- Production deploy requires explicit approval

### Next post-MVP options

1. Real production deploy (requires explicit approval)
2. PR automation (GitHub/GitLab integration)
3. Frontend web dashboard (React + Vite + shadcn/ui)
4. Telegram webhook mode (currently long-polling)
5. CI/CD remote pipeline (GitHub Actions / GitLab CI)
6. Observability: Sentry / Grafana / Prometheus / log rotation
7. Memory retrieval tuning: ranking quality + scope heuristics
8. Qdrant migration (from pgvector)
9. Agent permissions JSONB Phase 3 (API-level enforcement)

---

## Phase 0: Подготовка инфраструктуры — ✅ COMPLETE

**Цель:** Сервер готов, репозиторий создан, базовые сервисы запускаются.
**Статус:** COMPLETE (commit chain FND-01..FND-03, DOP-01..DOP-02)

### Задачи

| # | Задача | Статус | Evidence |
|---|--------|--------|----------|
| 0.1 | Создать monorepo, инициализировать git | ✅ COMPLETE | FND-01 |
| 0.2 | `docker-compose.yml`: PostgreSQL 16 + pgvector, Redis 7 | ✅ COMPLETE | DOP-01 |
| 0.3 | FastAPI каркас: `main.py`, `config.py`, lifespan, CORS | ✅ COMPLETE | FND-02 |
| 0.4 | SQLAlchemy модели: все таблицы | ✅ COMPLETE | FND-03 |
| 0.5 | Alembic: init + первая миграция | ✅ COMPLETE | FND-03 |
| 0.6 | `.env.example` с переменными | ✅ COMPLETE | DOP-03 Phase 2 |
| 0.7 | `AGENTS.md` для проекта | ✅ COMPLETE | FND-01 |
| 0.8 | Структура `.ai_memory/` vault | ✅ COMPLETE | FND-01 |

### Результат
- `docker compose up` поднимает PostgreSQL + Redis
- `uvicorn` запускает FastAPI с healthcheck `/health`
- Миграции накатываются через `alembic upgrade head`

---

## Phase 1: Telegram Routing — ✅ COMPLETE

**Цель:** Сообщения из топиков группы превращаются в задачи.
**Статус:** COMPLETE (TG-01..TG-06, BE-01..BE-03, live validated)

### Задачи

| # | Задача | Статус | Evidence |
|---|--------|--------|----------|
| 1.1 | Telegram bot gateway (aiogram 3.x) | ✅ COMPLETE | TG-01 |
| 1.2 | Topic binding + routing (`/bind_topic`, `/unbind_topic`) | ✅ COMPLETE | TG-02 |
| 1.3 | CRUD endpoints: `/projects`, `/agents`, `/topics` | ✅ COMPLETE | BE-01 |
| 1.4 | Tasks + Approvals domain | ✅ COMPLETE | BE-02 |
| 1.5 | Runtime adapter (plan-only) | ✅ COMPLETE | BE-03 |
| 1.6 | Approval cards UX (inline keyboards) | ✅ COMPLETE | TG-03 |
| 1.7 | Live integration (security, HTML fixes, private chat) | ✅ COMPLETE | TG-04 |
| 1.8 | Notifications + admin gate | ✅ COMPLETE | TG-05 |
| 1.9 | Compact callback protocol | ✅ COMPLETE | TG-06 |

### Результат
- Сообщение в topic создаёт Task в БД
- Bot отвечает в тот же topic
- `/bind_topic` привязывает topic к агенту или проекту
- Live E2E validated (private chat + inline approve/reject)
- Compact callback protocol (< 64 bytes, HMAC-signed)

---

## Phase 2: Project Memory — ✅ COMPLETE

**Цель:** У каждого проекта есть markdown-память с семантическим retrieval.
**Статус:** COMPLETE (MEM-01..MEM-04)

### Задачи

| # | Задача | Статус | Evidence |
|---|--------|--------|----------|
| 2.1 | Memory provisioning (templates, service, schemas) | ✅ COMPLETE | MEM-01 |
| 2.2 | Memory CRUD API (6 endpoints, access tiers) | ✅ COMPLETE | MEM-02 |
| 2.3 | Indexing + retrieval (chunking, embeddings, pgvector) | ✅ COMPLETE | MEM-03 |
| 2.4 | Mandatory memory checkpoints | ✅ COMPLETE | MEM-04 |

### Результат
- При добавлении проекта создаётся vault с шаблонами
- Memory индексируется и доступна через `/memory/search`
- Агенты могут искать релевантный контекст
- Memory checkpoint runbook and AGENTS.md rule #7

---

## Phase 3: OpenCode Runtime — ✅ COMPLETE

**Цель:** Агент получает задачу + память и возвращает план.
**Статус:** COMPLETE (BE-04..BE-12, real OpenCode 1.14.x smoke validated)

### Задачи

| # | Задача | Статус | Evidence |
|---|--------|--------|----------|
| 3.1 | RealOpenCodeHttpTransport (HTTP/SSE на httpx) | ✅ COMPLETE | BE-05 |
| 3.2 | Runtime guardrails (provider=stub default, fail-closed) | ✅ COMPLETE | BE-04 |
| 3.3 | OpenCode 1.14.x native contract alignment | ✅ COMPLETE | BE-07+ |
| 3.4 | Session traceability + timeout tuning | ✅ COMPLETE | BE-08 |
| 3.5 | Real OpenCode smoke: first plan_generated | ✅ COMPLETE | BE-08 real |
| 3.6 | Runtime reliability hardening | ✅ COMPLETE | BE-10 |
| 3.7 | Read-timeout alignment (SDK-compatible) | ✅ COMPLETE | BE-12 |

### Результат
- Агент отвечает планом на основе памяти проекта
- Real OpenCode 1.14.x adapter validated end-to-end
- Default provider=stub, explicit opt-in for real OpenCode
- All guardrails: plan-only, path confinement, redaction, max_plan_size, timeout

---

## Phase 4: Safe Code Execution — ✅ COMPLETE

**Цель:** Агент может менять код в изолированной ветке после approve.
**Статус:** COMPLETE (WRK-01..WRK-04, BE-06..BE-11, Docker sandbox validated)

### Задачи

| # | Задача | Статус | Evidence |
|---|--------|--------|----------|
| 4.1 | Celery worker skeleton (7 queues) | ✅ COMPLETE | WRK-01 |
| 4.2 | Plan pipeline (trigger-plan → agent_plan → notifications) | ✅ COMPLETE | WRK-02 |
| 4.3 | Safe execute pipeline (approved-only, policy, redaction) | ✅ COMPLETE | WRK-03 |
| 4.4 | Docker sandbox runner (opt-in, argv-only, dynamic mount) | ✅ COMPLETE | WRK-04 |
| 4.5 | Command policy (shell escape, chaining, network tools blocked) | ✅ COMPLETE | WRK-03 hardening |
| 4.6 | Real Docker smoke test (Scenario A: compileall) | ✅ COMPLETE | WRK-04 real docker |
| 4.7 | Worker timeout fix (SIGHUP, API_TIMEOUT) | ✅ COMPLETE | BE-09, WORKER-LINUX-01 |

### Результат
- Агент выполняет код в Docker sandbox
- Изменения в отдельном git worktree
- Tests запускаются автоматически
- Diff summary отправляется в Telegram
- Default: FakeSandboxRunner; real Docker requires explicit opt-in

---

## Phase 5: PR Workflow — ⏸ DEFERRED

**Цель:** Агент создаёт PR/MR.
**Статус:** NOT STARTED — deferred to post-MVP

### Задачи (planned)

| # | Задача | Агент | Риск |
|---|--------|-------|------|
| 5.1 | GitHub/GitLab API integration | backend-architect | medium |
| 5.2 | Push branch → create PR | git-workflow-master | medium |
| 5.3 | Attach summary to PR description | backend-architect | low |
| 5.4 | Save PR link в task record | backend-architect | low |

### Результат (target)
- Агент создаёт PR с описанием изменений
- PR link сохраняется в задаче

---

## Phase 6: DevOps/Deploy Foundation — 🔶 DRY-RUN VALIDATED

**Цель:** Production deployment infrastructure ready.
**Статус:** Templates and scripts created, dry-run validated. **Real deploy NOT executed.**

### Задачи

| # | Задача | Статус | Evidence |
|---|--------|--------|----------|
| 6.1 | Dev docker-compose (postgres+redis+api) | ✅ COMPLETE | DOP-01 |
| 6.2 | Dockerfiles + sandbox compose | ✅ COMPLETE | DOP-02 |
| 6.3 | Caddy reverse proxy template | ✅ COMPLETE | DOP-03 Phase 2 |
| 6.4 | systemd unit templates (api, worker, bot) | ✅ COMPLETE | DOP-03 Phase 2 |
| 6.5 | Production docker-compose template | ✅ COMPLETE | DOP-03 Phase 2 |
| 6.6 | Enhanced /health (DB + Redis checks) | ✅ COMPLETE | DOP-03 Phase 2 |
| 6.7 | Preflight / release / rollback / smoke scripts | ✅ COMPLETE | DOP-04 Phase 2 |
| 6.8 | Deploy validation script | ✅ COMPLETE | DOP-03 Phase 2 |
| 6.9 | Dry-run validation (all templates/scripts) | ✅ COMPLETE | DOP-03 Phase 3, DOP-04 Phase 3 |
| 6.10 | Real production deploy | ⏸ NOT EXECUTED | Requires explicit approval |

### Результат
- Production templates ready: Caddy, systemd, docker-compose.prod.yml, .env.example
- Release workflow scripts: preflight, release, rollback, smoke (all safe-by-default)
- All validation dry-runs PASS
- **Real production deploy requires explicit approval and has NOT been executed**

---

## Phase 7: Security/Approval/Deploy Safety — 🔶 DRY-RUN VALIDATED

**Цель:** Full security chain: permissions, audit trail, secrets safety, deploy gates.
**Статус:** Code complete, live-validated for security, dry-run validated for deploy.

### Задачи

| # | Задача | Статус | Evidence |
|---|--------|--------|----------|
| 7.1 | Permission engine (fail-closed, 14 actions) | ✅ COMPLETE | SEC-01 (live smoke PASS) |
| 7.2 | Security audit trail (model, migration, service, integration) | ✅ COMPLETE | SEC-02 (live smoke PASS) |
| 7.3 | Centralized secrets redaction (10 patterns) | ✅ COMPLETE | SEC-03 (live smoke PASS) |
| 7.4 | SQLAlchemy log safety (SQL_ECHO decoupled) | ✅ COMPLETE | SEC-03B |
| 7.5 | Approval gates (CONFIRM_PRODUCTION_DEPLOY, etc.) | ✅ COMPLETE | DOP-04 |
| 7.6 | Deploy validation (preflight, template checks) | ✅ COMPLETE | DOP-03, DOP-04 |
| 7.7 | Real production deploy with approval | ⏸ NOT EXECUTED | Requires explicit approval |

### Результат
- PermissionEngine: admin-gated approve/reject, risk-level gating
- SecurityAuditService: append-only, 21 columns, redacted metadata
- Centralized redaction: 10 secret patterns, unified across 4 systems
- Deploy gates: CONFIRM_PRODUCTION_DEPLOY, CONFIRM_MIGRATIONS, CONFIRM_SERVICE_RESTART
- **Production deploy impossible without explicit approval**

---

## Phase 8: Web Dashboard — ⏸ NOT STARTED / v2

**Цель:** Web UI в стиле Mission Control.
**Статус:** NOT STARTED — deferred to v2

### Задачи (planned)

| # | Задача | Агент | Риск |
|---|--------|-------|------|
| 8.1 | React + Vite + TailwindCSS + shadcn/ui setup | frontend-developer | low |
| 8.2 | Agents list page | frontend-developer | low |
| 8.3 | Task queue с SSE/WebSocket live updates | frontend-developer | medium |
| 8.4 | Project cards page | frontend-developer | low |
| 8.5 | Memory file viewer | frontend-developer | medium |
| 8.6 | Approval management page | frontend-developer | medium |
| 8.7 | System status / health | frontend-developer | low |
| 8.8 | SSE endpoint в FastAPI | backend-architect | medium |

### Результат (target)
- Полноценный web dashboard
- Live updates через SSE/WebSocket
- Все операции доступны через UI

---

## Критерии завершения MVP

### Completed MVP DoD items

- [x] Telegram bot принимает сообщения из forum topics
- [x] Topic корректно маппится на агента или проект
- [x] Можно зарегистрировать проект
- [x] Для проекта создаётся markdown memory vault
- [x] Memory индексируется и доступна через search
- [x] Агент получает задачу и возвращает plan
- [x] Агент выполняет approved-задачу в git worktree
- [x] Команды запускаются в sandbox
- [x] Bot возвращает diff summary и test results
- [x] Результат задачи записывается в memory
- [x] Production deploy невозможен без approval (gates implemented, dry-run validated)

### Deploy-specific DoD distinction

- [x] Production runtime templates created and dry-run validated
- [x] Release workflow scripts (preflight/release/rollback/smoke) created and dry-run validated
- [x] Deploy validation script confirms safety (ALL CHECKS PASSED)
- [ ] **Real production deploy NOT executed** — requires explicit approval and real VPS

### Negative safety item (must remain clear)

- **No production deploy without approval** — confirmed: CONFIRM_PRODUCTION_DEPLOY gate is fail-closed
- **No secrets in templates/logs** — confirmed: centralized redaction, SQL_ECHO decoupled, 10-pattern coverage
