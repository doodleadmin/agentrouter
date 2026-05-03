# DevOps Plan: Controlled Smoke Test — Real OpenCode Server (Plan-Only)

**Агент:** devops-automator  
**Дата:** 2026-05-04  
**Статус:** plan-only (ничего не запущено, ничего не менялось)  
**Риск:** low (только документ-план, без исполнения)

---

## Контекст

BE-03 и BE-04 реализовали runtime adapter слой с контрактом `OpenCodeClientProtocol`:
- `StubOpenCodeClient` — детерминированный fake для тестов (default, `RUNTIME_PROVIDER=stub`)
- `OpenCodeHttpPlanClient` — real HTTP/SSE client для `RUNTIME_PROVIDER=opencode_http`, требует валидный `OPENCODE_SERVER_URL`

На данный момент **реальный OpenCode server никогда не запускался**. Все тесты используют `FakeOpenCodeHttpClient` (in-memory) или `StubOpenCodeClient`. Задача: составить план controlled smoke test локального OpenCode server, который будет принимать plan-only запросы и отвечать SSE-стримом.

**Smoke test = минимальная проверка**: сервер запущен, слушает порт, принимает POST `/session` + GET `/session/{id}/events` (SSE), и наш `OpenCodeHttpPlanClient` успешно получает `plan.delta` + `plan.final` события через реальную сеть (localhost).

---

## 1. Как запустить OpenCode server локально

### 1.1 Способ запуска

**Вариант A — локальный процесс (node/npx):**  
OpenCode распространяется как npm-пакет (`@opencode-ai/plugin` уже есть в `.opencode/package.json` версии `1.4.3`). Сервер запускается командой:

```bash
npx opencode-server --port 3001 --mode plan-only
```

Или через standalone binary (если есть `opencode` CLI):

```bash
opencode server start --port 3001 --mode plan-only
```

**Вариант B — Docker (рекомендуемый для sandbox isolation):**  
Если OpenCode опубликован как Docker image (гипотетический `opencode/server:latest`):

```bash
docker run --rm --name amc-opencode-smoke -p 3001:3001 opencode/server:latest --port 3001 --mode plan-only
```

**Решение (для плана):** Для локальной машины (Windows 11, Docker Desktop доступен) предпочтителен Docker-вариант — изоляция чище, cleanup проще. Если официального образа нет, подойдёт локальный процесс через `npx`.

### 1.2 Порт

**Рекомендуемый порт: `3001`** (не конфликтует с API:8000, Telegram:8443, React:3000, postgres:5432, redis:6379).

### 1.3 Минимальная конфигурация для plan-only режима

Сервер должен поддерживать минимум два endpoint:
1. `POST /session` — создать сессию (принимает payload с `mode: "plan_only"`)
2. `GET /session/{session_id}/events` — SSE stream с событиями `plan.delta` и `plan.final`

**Флаги запуска:**
- `--mode plan-only` — запрет на execute/tool/mutate операции
- `--port 3001`
- `--host 0.0.0.0` (или `127.0.0.1` для local-only safety)

### 1.4 Переменные окружения на стороне OpenCode server

Если сервер использует API ключи для LLM (OpenAI, Anthropic):
- `OPENAI_API_KEY` — если сервер вызывает OpenAI под капотом
- `ANTHROPIC_API_KEY` — если сервер вызывает Anthropic
- `OPENCODE_LOG_LEVEL=info`
- `OPENCODE_MODE=plan_only`

**Важно:** Эти переменные **не** являются частью `.env` проекта Agent Router. Они передаются в контейнер/процесс OpenCode напрямую и **никогда** не пишутся в файлы проекта.

---

## 2. Что нужно в docker-compose / sandbox (если применимо)

### 2.1 Минимальный compose-файл для smoke test OpenCode

**НЕ создавать без approve.** Ниже — план (text-only).

```yaml
# План (не создавать без approve):
# infra/docker/opencode-smoke.compose.yml

services:
  opencode-server:
    image: opencode/server:latest          # или build: .opencode/
    container_name: amc-smoke-opencode
    ports:
      - "127.0.0.1:3001:3001"              # ТОЛЬКО localhost
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}     # из .env.opencode-smoke (НЕ из .env проекта)
      OPENCODE_MODE: plan_only
      OPENCODE_LOG_LEVEL: info
    command: ["--port", "3001", "--mode", "plan-only"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1:3001/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s
    restart: "no"
    networks:
      - agentrouter_dev_net
    # Без volumes, без docker.sock, без privileged
    mem_limit: 1g
    cpus: 1.0
    pids_limit: 64
    read_only: true
    tmpfs:
      - /tmp:size=32m
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
```

**Альтернативно** (если образ недоступен, только локальный процесс):

OpenCode server запускается напрямую на хосте через `npx` — compose не нужен, но это менее изолированно. Допустимо для smoke test, так как режим plan-only и только localhost.

### 2.2 Network / Memory / Volume ограничения

| Параметр | Значение | Причина |
|----------|----------|---------|
| `ports` | `127.0.0.1:3001:3001` | Только localhost, не наружу |
| `network` | `agentrouter_dev_net` | Внутренняя bridge-сеть проекта |
| `mem_limit` | `1g` | Достаточно для LLM inference |
| `cpus` | `1.0` | Минимально для smoke test |
| `pids_limit` | `64` | Предотвращение fork-бомб |
| `read_only` | `true` | Файловая система только на чтение |
| `tmpfs` | `/tmp:size=32m` | Только временная запись |
| `volumes` | **нет** | Никаких монтирований из проекта |
| `secrets` | **нет** | Никаких docker secrets |
| `cap_drop` | `ALL` | Минимальные capabilities |
| `no-new-privileges` | `true` | Запрет повышения привилегий |

### 2.3 Healthcheck

```bash
# Ожидаемый endpoint
curl -f http://127.0.0.1:3001/health
# Ожидаемый ответ: {"status": "ok", "mode": "plan_only"}
```

Если `/health` не реализован в OpenCode сервере, альтернатива:
```bash
curl -f http://127.0.0.1:3001/  # любой non-5xx ответ = сервер жив
```

---

## 3. Что нужно в .env (только план, не менять)

### 3.1 НЕ трогать существующие файлы

Запрещено создавать или изменять `.env` в корне проекта. Вместо этого для smoke test создаётся **отдельный временный файл** `.env.opencode-smoke` (не коммитится, уже в `.gitignore` через паттерн `.env.*`).

### 3.2 Переменные в `.env.opencode-smoke`

```bash
# .env.opencode-smoke (временный, только для manual smoke test, удаляется после cleanup)
OPENAI_API_KEY=sk-...           # передаётся в контейнер OpenCode, НЕ в агентов AMC
OPENCODE_MODE=plan_only
```

### 3.3 Переменные в существующем `.env` (если будет создан)

Эти переменные уже ожидаются конфигурацией `apps/api/app/config.py`:

```bash
RUNTIME_PROVIDER=opencode_http     # default=stub → переключить на opencode_http
OPENCODE_SERVER_URL=http://127.0.0.1:3001   # URL запущенного сервера
RUNTIME_SESSION_TIMEOUT_SECONDS=60
RUNTIME_IDLE_TIMEOUT_SECONDS=20
RUNTIME_MAX_RETRIES=2
```

**Важно:** `RUNTIME_PROVIDER=opencode_http` включается **только на время smoke test**. После завершения теста значение должно быть возвращено в `stub` (default).

### 3.4 Что НЕ менять

- Не добавлять `OPENAI_API_KEY` в `.env` проекта (агенты не должны видеть API ключи)
- Не менять `RUNTIME_ALLOWED_ROOT` (остаётся `.`)
- Не менять `RUNTIME_MEMORY_TOP_K` (остаётся `5`)

---

## 4. Checks перед запуском

### 4.1 Pre-flight checks (до старта OpenCode server)

| # | Проверка | Команда | Ожидаемый результат |
|---|----------|---------|---------------------|
| 1 | Порт 3001 свободен | `netstat -ano \| findstr :3001` (Windows) | Нет процесса на порту |
| 2 | Docker Desktop запущен | `docker info` | Server Version: ... |
| 3 | Текущий `RUNTIME_PROVIDER` = `stub` | `grep RUNTIME_PROVIDER .env` (если .env есть) | `stub` или отсутствует (default) |
| 4 | `SANDBOX_RUNNER_MODE` = `fake` | `grep SANDBOX_RUNNER_MODE .env` | `fake` или отсутствует (default) |
| 5 | OpenCode server доступен (образ/бинарь) | `docker pull opencode/server:latest` или `npx opencode-server --version` | Success |
| 6 | Нет запущенных контейнеров amc-smoke-* | `docker ps --filter name=amc-smoke` | Empty |
| 7 | `.env.opencode-smoke` создан и переопределяет только API key | `type .env.opencode-smoke` (Windows) | Только `OPENAI_API_KEY` и `OPENCODE_MODE` |
| 8 | `.gitignore` игнорирует `.env.opencode-smoke` | Проверить `.gitignore` | Паттерн `.env.*` уже есть ✅ |

### 4.2 Post-start checks (после запуска OpenCode server)

| # | Проверка | Команда/Endpoint | Ожидаемый результат |
|---|----------|-----------------|---------------------|
| 1 | Health endpoint | `curl http://127.0.0.1:3001/health` | HTTP 200, `{"status":"ok"}` |
| 2 | Создать plan-only сессию | `curl -X POST http://127.0.0.1:3001/session -H 'Content-Type: application/json' -d '{"mode":"plan_only","input":{"task":"test"}}'` | HTTP 200, `{"session_id":"..."}` |
| 3 | SSE stream доступен | `curl -N http://127.0.0.1:3001/session/{session_id}/events` | SSE поток с `data: {"type":"plan.delta",...}` |
| 4 | Сервер в plan-only режиме | Проверить логи контейнера | `OPENCODE_MODE=plan_only` в выводе |
| 5 | Порт не exposed наружу | `docker port amc-smoke-opencode` | `3001/tcp -> 127.0.0.1:3001` (только localhost) |
| 6 | Нет монтированных volumes | `docker inspect amc-smoke-opencode --format '{{.Mounts}}'` | `[]` (пусто) |

### 4.3 Application-level smoke test (через AMC API + реальный OpenCode)

| # | Проверка | Действие | Ожидаемый результат |
|---|----------|----------|---------------------|
| 1 | Переключить `RUNTIME_PROVIDER` на `opencode_http` | `$env:RUNTIME_PROVIDER="opencode_http"` (временный override для одного процесса) | `settings.RUNTIME_PROVIDER == "opencode_http"` |
| 2 | Установить `OPENCODE_SERVER_URL` | `$env:OPENCODE_SERVER_URL="http://127.0.0.1:3001"` | `settings.OPENCODE_SERVER_URL == "http://127.0.0.1:3001"` |
| 3 | Создать low-risk задачу | `POST /tasks` + `POST /runtime/tasks/{id}/plan` | HTTP 200, `plan_text` непустой, `status=approved` |
| 4 | План содержит реальный контент (не stub) | Проверить `plan_text` на шаблон StubOpenCodeClient | Не содержит фразы из заглушки (например, "stub-session") |
| 5 | События логгированы | `GET /events/tasks/{id}/events` | `runtime_session_created`, `plan_generated`, `runtime_event_received` |
| 6 | Redaction работает | Проверить текст плана | Нет `[REDACTED]` утечек (секреты не передавались) |

---

## 5. Cleanup plan

### 5.1 Остановка OpenCode server

**Docker вариант:**
```bash
docker stop amc-smoke-opencode && docker rm amc-smoke-opencode
```

**Локальный процесс (npx):**
```bash
# Ctrl+C в терминале, где запущен сервер
# Или:
taskkill /F /PID <pid>  # Windows
```

### 5.2 Удаление артефактов

| # | Действие | Команда |
|---|----------|---------|
| 1 | Удалить контейнер | `docker rm -f amc-smoke-opencode` |
| 2 | Удалить образ (если не нужен) | `docker rmi opencode/server:latest` (опционально) |
| 3 | Удалить `.env.opencode-smoke` | `del .env.opencode-smoke` (Windows) |
| 4 | Вернуть `RUNTIME_PROVIDER=stub` | Убрать override или вернуть в `.env` значение `stub` |
| 5 | Вернуть `OPENCODE_SERVER_URL=""` | Пустая строка в `.env` |
| 6 | Удалить network (если не shared) | `docker network rm amc_dev_net` (только если больше не нужен) |
| 7 | Проверить нет orphan-процессов | `docker ps` и `netstat -ano \| findstr :3001` |

### 5.3 Убедиться что нет остаточных артефактов

- [ ] `docker ps --filter name=amc-smoke` → пусто
- [ ] `netstat -ano | findstr :3001` → пусто
- [ ] `.env.opencode-smoke` → файл удалён
- [ ] `RUNTIME_PROVIDER` → `stub` (default, без override)
- [ ] `OPENCODE_SERVER_URL` → пустая строка или не задана
- [ ] В `.ai_memory/` нет записей с реальными API ключами (redaction check)
- [ ] В `task_events` нет записей с реальными API ключами
- [ ] `SANDBOX_RUNNER_MODE` → `fake`
- [ ] `SANDBOX_MANUAL_TEST_MODE` → `False`

### 5.4 Rollback если что-то пошло не так

```bash
# Если OpenCode server завис:
docker kill amc-smoke-opencode && docker rm amc-smoke-opencode

# Если порт 3001 остался занят (Windows):
netstat -ano | findstr :3001
taskkill /F /PID <pid>

# Если .env испорчен (маловероятно — мы его не меняем):
# Восстановить из git: git checkout .env
```

---

## 6. Что запрещено

### 6.1 Абсолютные запреты (never)

- ❌ **Не трогать production/staging** — smoke test только на localhost
- ❌ **Не менять существующие docker-compose файлы** — `infra/docker/docker-compose.yml` и `sandbox.compose.yml` остаются нетронутыми
- ❌ **Не открывать порты наружу** — OpenCode server слушает только `127.0.0.1:3001`
- ❌ **Не создавать `.env` в корне проекта** — только `.env.opencode-smoke` (временный, gitignored)
- ❌ **Не добавлять API ключи в `.env` проекта** — ключи только в `.env.opencode-smoke`
- ❌ **Не запускать deploy, миграции, DB операции** — smoke test не требует БД
- ❌ **Не монтировать проект в OpenCode контейнер** — никаких volumes
- ❌ **Не использовать `privileged: true`** — контейнер без привилегий
- ❌ **Не подключать `docker.sock`** — контейнер не управляет Docker
- ❌ **Не оставлять `RUNTIME_PROVIDER=opencode_http` после теста** — обязательно вернуть `stub`

### 6.2 Условные запреты (требуют approve)

- ⚠️ Создание нового compose-файла `infra/docker/opencode-smoke.compose.yml` — **требует approve** (medium: новый инфра-файл)
- ⚠️ Модификация `apps/api/app/config.py` — **требует approve** (medium: изменение конфигурации)
- ⚠️ Установка новых npm-пакетов в `.opencode/package.json` — **требует approve** (medium: изменение зависимостей)
- ⚠️ Создание нового transport adapter для real HTTP (не fake) — **требует approve** (medium: изменение runtime-пути)

### 6.3 Что разрешено без approve

- ✅ План (этот документ)
- ✅ Ручной запуск OpenCode server на localhost через Docker/npx (не затрагивает проект)
- ✅ Ручные `curl` запросы к OpenCode server для проверки health/SSE
- ✅ Временный environment variable override в терминале (`$env:KEY="value"` — только для одного powershell сеанса)
- ✅ Cleanup после теста

---

## 7. Sequence — порядок действий при реальном выполнении

```
1. PRE-FLIGHT (read-only checks)
   ├── Проверить порт 3001 свободен
   ├── Проверить Docker Desktop запущен
   ├── Проверить текущий RUNTIME_PROVIDER=stub
   └── Проверить SANDBOX_RUNNER_MODE=fake

2. CREATE TEMP CONFIG
   ├── Создать .env.opencode-smoke (временный)
   └── Убедиться что .gitignore ловит этот файл

3. START OPENCODE SERVER
   ├── docker run --rm -d --name amc-smoke-opencode \
   │     -p 127.0.0.1:3001:3001 \
   │     --env-file .env.opencode-smoke \
   │     opencode/server:latest --port 3001 --mode plan-only
   └── Дождаться healthcheck (curl /health)

4. SMOKE TEST — RAW HTTP
   ├── curl POST /session (создать сессию)
   ├── curl GET /session/{id}/events (получить SSE)
   └── Проверить что события приходят

5. SMOKE TEST — AMC INTEGRATION (опционально, требует approve для конфиг-изменений)
   ├── Временно переопределить RUNTIME_PROVIDER=opencode_http
   ├── Временно переопределить OPENCODE_SERVER_URL=http://127.0.0.1:3001
   ├── Запустить AMC API
   ├── POST /tasks (low-risk)
   ├── POST /runtime/tasks/{id}/plan
   └── Проверить plan_text не из заглушки

6. CLEANUP
   ├── docker stop amc-smoke-opencode
   ├── docker rm amc-smoke-opencode
   ├── del .env.opencode-smoke
   ├── Убрать временные env override
   ├── Проверить что порт 3001 свободен
   └── Проверить что RUNTIME_PROVIDER=stub
```

---

## 8. Риски

| Риск | Вероятность | Влияние | Mitigation |
|------|-------------|---------|------------|
| OpenCode server image недоступен | Medium | Блокирует Docker-вариант | Fallback: локальный npx-процесс |
| API ключ невалидный / нет кредитов | Medium | Сервер запущен, но LLM не отвечает | Проверить ключ отдельным curl к OpenAI API |
| Порт 3001 уже занят | Low | Блокирует запуск | Проверить перед стартом, выбрать другой порт |
| OpenCode SSE формат несовместим с нашим клиентом | Medium | План-стрим не парсится | Задокументировать разницу, адаптировать `OpenCodeHttpPlanClient` (требует approve) |
| Docker Desktop не запущен на Windows | Low | Блокирует Docker-вариант | Fallback: локальный npx-процесс |
| Забыли вернуть `RUNTIME_PROVIDER=stub` | Medium | Production поведение изменено | Явный cleanup checklist; проверка после теста |

---

## 9. Approve gates (что требует подтверждения перед выполнением)

| # | Действие | Approve нужен? |
|---|----------|----------------|
| 1 | Создание `infra/docker/opencode-smoke.compose.yml` | **Да** (medium: новый инфра-файл) |
| 2 | Запуск `docker run` для OpenCode server | **Нет** (не затрагивает проект) |
| 3 | Ручные `curl` запросы к localhost | **Нет** (read-only) |
| 4 | Создание `.env.opencode-smoke` | **Нет** (временный, gitignored) |
| 5 | Изменение `apps/api/app/config.py` | **Да** (medium: изменение кода) |
| 6 | Создание real HTTP transport adapter | **Да** (medium: изменение runtime-пути) |
| 7 | Запуск AMC API с `opencode_http` | **Да** (medium: изменение конфигурации) |
| 8 | Cleanup (удаление контейнера, `.env.opencode-smoke`) | **Нет** |
