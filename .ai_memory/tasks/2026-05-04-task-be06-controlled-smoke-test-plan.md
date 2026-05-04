---
type: task
task_id: BE-06
status: plan-only
risk: high
requires_approval: true
date: '2026-05-04'
agent: studio-orchestrator
---
# BE-06: Controlled Real OpenCode Smoke Test — Plan/Preflight

**Дата:** 2026-05-04
**Статус:** PLAN-ONLY — ничего не запускается, ничего не меняется
**Риск:** HIGH (требует отдельного approve перед выполнением)
**Цель:** Подготовить и задокументировать процедуру первого реального smoke test OpenCode HTTP adapter в plan-only режиме

---

## 1. Текущее состояние системы

### 1.1 Git
- HEAD: `f7239de` — `feat(runtime): harden OpenCode transport safety gates`
- Working tree: clean (0 untracked/modified)
- Все 205 тестов проходят

### 1.2 Runtime конфигурация (default, безопасная)
```
RUNTIME_PROVIDER = "stub"                              # config.py:60
OPENCODE_SERVER_URL = ""                               # config.py:61
RUNTIME_ALLOW_REAL_OPENCODE_HTTP = False               # config.py:62
RUNTIME_ALLOWED_ROOT = "."                             # config.py:63
RUNTIME_MEMORY_TOP_K = 5                               # config.py:64
RUNTIME_SESSION_TIMEOUT_SECONDS = 60                   # config.py:65
RUNTIME_IDLE_TIMEOUT_SECONDS = 20                      # config.py:66
RUNTIME_MAX_RETRIES = 2                                # config.py:67
RUNTIME_MAX_PLAN_BYTES = 100_000                       # config.py:68
```

### 1.3 Безопасность (подтверждено security-engineer)
- Triple opt-in для реального transport: `provider=opencode_http` + `URL` + `allow=true`
- Unknown provider → fail-closed
- Missing URL → fail-closed
- Missing allow flag → fail-closed
- Plan-only boundary: only `read/search/analyze/plan` tool actions
- SSE chunk limit: 64KB per non-JSON chunk
- Max plan size: 100KB with safe truncation
- Dual timeout: session (60s) + idle (20s) at transport AND client layers
- Value-level redaction on all outputs
- Tool.call path confinement for read/search actions

---

## 2. Предварительные условия для smoke test

### 2.1 OpenCode server доступен

Необходимо установить/запустить OpenCode server на `127.0.0.1:3001` (или `4242`).

**Варианты:**
- **A (Docker):** `docker run --rm -d --name amc-smoke-opencode -p 127.0.0.1:3001:3001 opencode/server:latest`
- **B (npx):** `npx @opencode/server --port 3001`
- **C (binary):** `opencode server --port 3001`

> ⚠️ Выбор варианта и запуск — **требует отдельного approve**.

**Pre-start проверки:**
- [ ] Порт 3001 свободен: `netstat -an | findstr :3001` (Windows)
- [ ] Docker Desktop запущен (если вариант A)
- [ ] OpenCode server образ/бинарь доступен
- [ ] Нет residual контейнеров `amc-smoke-*`

**Post-start проверки:**
- [ ] `GET http://127.0.0.1:3001/health` → HTTP 200
- [ ] `POST http://127.0.0.1:4096/session` → `{"session_id": "..."}`
- [ ] `POST http://127.0.0.1:4096/session/{id}/message` → JSON response with `parts`
- [ ] Сервер слушает только на localhost (не 0.0.0.0)

### 2.2 AMC API server запущен

```
cd apps/api
uvicorn app.main:app --reload --port 8000
```

Pre-checks:
- [ ] `GET http://localhost:8000/health` → 200
- [ ] PostgreSQL запущен (docker compose)
- [ ] Redis запущен (docker compose)

---

## 3. Временные env override (только на время теста)

**Способ:** env vars при запуске API (НЕ через .env файл):

```bash
# Windows PowerShell
$env:RUNTIME_PROVIDER="opencode_http"
$env:OPENCODE_SERVER_URL="http://127.0.0.1:3001"
$env:RUNTIME_ALLOW_REAL_OPENCODE_HTTP="true"

# Запуск API с override
cd apps/api
uvicorn app.main:app --reload --port 8000
```

**ИЛИ:** создать временный `.env.smoke` (gitignored):

```env
RUNTIME_PROVIDER=opencode_http
OPENCODE_SERVER_URL=http://127.0.0.1:3001
RUNTIME_ALLOW_REAL_OPENCODE_HTTP=true
RUNTIME_SESSION_TIMEOUT_SECONDS=30
RUNTIME_IDLE_TIMEOUT_SECONDS=10
```

> ⚠️ Создание `.env.smoke` — **не менять `.env` проекта**.

### 3.1 Что НЕ меняется
- [x] `RUNTIME_ALLOWED_ROOT` остаётся `.`
- [x] `RUNTIME_MEMORY_TOP_K` остаётся `5`
- [x] `RUNTIME_MAX_PLAN_BYTES` остаётся `100_000`
- [x] `RUNTIME_MAX_RETRIES` остаётся `2`
- [x] SANDBOX переменные НЕ трогаются
- [x] `.env` проекта НЕ создаётся/меняется

---

## 4. Безопасная тестовая задача (low-risk)

### 4.1 Task definition

```
Title: "Analyze project structure and plan a healthcheck endpoint"
Risk Level: low
Project: (зарегистрированный project в AMC)
Agent: backend-architect
```

### 4.2 Промпт (безопасный, plan-only)

```
Analyze the current project structure in the repository.
Identify the main modules and their responsibilities.
Create a plan for adding a simple healthcheck endpoint
to the FastAPI application that returns {"status": "ok"}.

Do NOT write or modify any files.
Do NOT run any commands.
Only read project files and produce a plan.
```

### 4.3 Запрещённые слова в промпте (подтверждение)
- ❌ write, edit, modify, create, delete, remove
- ❌ bash, shell, command, execute, run, script
- ❌ deploy, staging, production, server
- ❌ git, commit, push, pull, branch, merge
- ❌ migrate, migration, alembic, schema
- ❌ env, .env, secret, token, password, key, credential
- ❌ docker, compose, container, image
- ❌ npm, pip, install
- ❌ curl, wget, http://, https:// (внешние)

### 4.4 API calls для smoke test

```bash
# 1. Создать task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Analyze project structure and plan a healthcheck endpoint",
    "raw_text": "Analyze the current project structure. Create a plan for adding a healthcheck endpoint. Do NOT write or modify any files. Only read and plan.",
    "risk_level": "low",
    "project_id": "<project-uuid>",
    "agent_id": "<agent-uuid>"
  }'

# 2. Trigger plan generation
curl -X POST http://localhost:8000/runtime/tasks/<task-id>/plan

# 3. Check task status + events
curl http://localhost:8000/tasks/<task-id>
curl http://localhost:8000/events/tasks/<task-id>/events
```

---

## 5. Expected event flow (успешный сценарий)

| # | Event Type | Источник | Описание |
|---|-----------|----------|----------|
| 1 | `runtime_session_created` | runtime_service | OpenCode session создана |
| 2..N | `runtime_event_received` | client | Каждое SSE событие от OpenCode (plan.delta × N) |
| 3 | `plan_generated` | runtime_service | План успешно получен |
| 4 | (auto-approved) | runtime_service | risk=low → status=approved |

**Expected task outcome:**
- `status` = `approved` (low risk auto-approve)
- `plan_text` = non-empty, contains plan structure
- `plan_text` does NOT contain stub fingerprint ("plan-only", "No code execution")

---

## 6. Abort criteria (НЕМЕДЛЕННАЯ остановка)

| # | Условие | Почему |
|---|---------|--------|
| A1 | **tool.call с запрещённым action** (write/edit/bash/deploy/git) НЕ блокируется | Plan-only boundary breach |
| A2 | **Разрешённый tool.call** (read/search/analyze/plan) ошибочно блокируется | False positive |
| A3 | **Файловые мутации:** `git status --porcelain` показывает изменения | Write invariant breach |
| A4 | **Secrets leak:** unredacted token/password/key в plan_text или task_events | Redaction failure |
| A5 | **Silent fallback на stub:** plan_text содержит stub fingerprint | Transport integrity breach |
| A6 | **Approval bypass:** medium+ risk task approved без approval | Approval invariant breach |
| A7 | **Сеть наружу:** OpenCode server обращается к внешним адресам | Network boundary breach |
| A8 | **Memory chunks > top-k:** request payload > 5 chunks | Memory minimization breach |
| A9 | **Plan > 100KB без truncation event:** plan_text exceeds limit | Size invariant breach |
| A10 | **Task застрял** в intermediate status (planning/running) > 60s | Timeout failure |

---

## 7. Post-smoke validation

### 7.1 task_events SQL проверка

```sql
SELECT event_type, payload, created_at FROM task_events
WHERE task_id = '<smoke-task-id>'
ORDER BY created_at;
```

Проверить:
- [ ] `runtime_session_created` присутствует
- [ ] `plan_generated` присутствует
- [ ] Нет `policy_blocked` для read/search/analyze/plan
- [ ] Нет raw секретов в payload
- [ ] Нет `deploy_*` событий
- [ ] Нет `command_started/command_finished` событий
- [ ] Нет `sandbox_*` событий
- [ ] `runtime_retry_scheduled` ≤ 2 (если есть)

### 7.2 plan_text проверка

- [ ] `LENGTH(plan_text) > 0`
- [ ] Contains substructure (headings `##`)
- [ ] No stub fingerprint ("plan-only", "No code execution")
- [ ] No raw secrets (search for token=, password=, Bearer, -----BEGIN.*PRIVATE)
- [ ] No embedded shell commands (bash, eval, exec, backticks)
- [ ] `payload->>'runtime_plan'` содержит correlation_id, session_id, idempotency_key

### 7.3 Database mutation check

```sql
SELECT count(*) FROM tasks WHERE id = '<smoke-id>';  -- = 1
SELECT status FROM tasks WHERE id = '<smoke-id>';     -- IN ('approved', 'waiting_approval', 'failed')
SELECT count(*) FROM approvals WHERE task_id = '<smoke-id>';  -- 0 для low risk
```

- [ ] Только 1 task row
- [ ] Status в valid end state
- [ ] Approval row для medium+ risk only (low = 0)
- [ ] No new projects/agents created (count before = count after)

### 7.4 Filesystem check

```bash
git status --porcelain                    # Empty
git diff --stat .ai_memory/               # Empty
git diff --stat apps/                     # Empty
```

- [ ] `git status --porcelain` = empty
- [ ] `.env` unchanged (not created)
- [ ] `.worktrees/` unchanged
- [ ] `.ai_memory/` no unexpected changes

---

## 8. Cleanup procedure (после smoke test)

```bash
# 1. Stop OpenCode server
docker stop amc-smoke-opencode 2>$null; docker rm amc-smoke-opencode 2>$null

# 2. Stop API server (Ctrl+C)

# 3. Reset env vars
Remove-Item Env:RUNTIME_PROVIDER -ErrorAction SilentlyContinue
Remove-Item Env:OPENCODE_SERVER_URL -ErrorAction SilentlyContinue
Remove-Item Env:RUNTIME_ALLOW_REAL_OPENCODE_HTTP -ErrorAction SilentlyContinue

# 4. Verify defaults restored
python -c "from apps.api.app.config import Settings; s = Settings(); assert s.RUNTIME_PROVIDER == 'stub'; assert not s.RUNTIME_ALLOW_REAL_OPENCODE_HTTP; assert s.OPENCODE_SERVER_URL == ''; print('OK: defaults restored')"

# 5. Delete temp .env.smoke if created
Remove-Item .env.smoke -ErrorAction SilentlyContinue

# 6. Verify port 3001 free
netstat -an | findstr :3001   # Should return nothing

# 7. Run full test suite
cd apps/api; python -m pytest tests -v   # Expect 205/205

# 8. Verify git clean
git status --porcelain   # Should be empty
```

---

## 9. Файлы, которые НЕ меняются

В рамках BE-06 plan/preflight **никакие файлы не меняются**. Это read-only план.

При выполнении (после approve) могут потребоваться:
- Временный `.env.smoke` (gitignored, удалается после теста)
- Возможное обновление `docs/smoke-test-opencode.md` (косметика)

---

## 10. Что категорически запрещено

| Запрещено | Причина |
|-----------|---------|
| ❌ Запускать OpenCode server без approve | medium-risk: внешний процесс |
| ❌ Менять `.env` проекта | Security: secrets risk |
| ❌ Менять `RUNTIME_PROVIDER` permanently | Production safety |
| ❌ Добавлять write/edit/bash/deploy в ALLOWED_PLAN_ACTIONS | Plan-only violation |
| ❌ Менять config.py defaults | Safety regression |
| ❌ Создавать DB миграции | Out of scope |
| ❌ Делать deploy | Out of scope |
| ❌ Трогать production/staging | Security |
| ❌ Открывать порты наружу (0.0.0.0) | Network boundary |

---

## 11. Требуется approve перед выполнением

BE-06 execution требует **отдельного approve** на:
1. Запуск OpenCode server (вариант A/B/C)
2. Временный env override (RUNTIME_PROVIDER, OPENCODE_SERVER_URL, RUNTIME_ALLOW_REAL_OPENCODE_HTTP)
3. Создание `.env.smoke` (если используется)

---

## 12. Risk classification

| Dimension | Rating | Rationale |
|-----------|--------|-----------|
| Overall risk | MEDIUM | External system, but plan-only + localhost + all guardrails |
| Network exposure | LOW | localhost only |
| Data leak | MEDIUM | Memory chunks + task context sent to server |
| Mutation risk | LOW | Plan-only path has no write/sandbox/execute |
| Guardrail strength | HIGH | 205 tests, triple opt-in, all 10 security checks passed |
| Rollback complexity | LOW | Env var switch, no DB changes, no deploy |

---

## 13. Rerun addendum (after step-B abort)

Дата: 2026-05-04  
Статус: PLAN-ONLY update (без запуска)

### 13.1 Новая стратегия порта
- Primary port: `4096`
- Fallback port: `4097`
- Порт `3001` больше не используется в BE-06 rerun

### 13.2 Обязательная команда запуска OpenCode

```bash
opencode serve --port <PORT> --hostname 127.0.0.1
```

### 13.3 Endpoint identity checks (rerun)
- Required: `GET http://127.0.0.1:<PORT>/global/health`
- Required: `GET http://127.0.0.1:<PORT>/doc`
- Optional: `GET http://127.0.0.1:<PORT>/config` или `GET http://127.0.0.1:<PORT>/agent`

### 13.4 Explicit rerun prohibitions
- ❌ Не использовать `opencode/server`
- ❌ Не использовать `@opencode/server`
- ❌ Не использовать bind `0.0.0.0`

### 13.5 Backend transport compatibility preflight
На корне `OPENCODE_SERVER_URL` должны быть доступны:
- `POST /session`
- `POST /session/{id}/message`

Проверка перед интеграционным smoke:
- [ ] `/global/health` отвечает корректно
- [ ] `/doc` отвечает корректно
- [ ] `POST /session` возвращает `session_id`
- [ ] `POST /session/{id}/message` возвращает JSON с `parts`

### 13.6 Cleanup invariant (без изменений)
После завершения/abort всегда восстановить defaults:
- `RUNTIME_PROVIDER=stub`
- `OPENCODE_SERVER_URL=""`
- `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=false`
