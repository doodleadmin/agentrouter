# Task: BE-06 FINAL EXECUTION — Controlled OpenCode Smoke Test (Real)

Дата: 2026-05-04
Агент: knowledge-steward (memory update), backend-architect (execution), studio-orchestrator (coordination)
Проект: agentrouter

---

## Постановка задачи

Execute the BE-06 controlled smoke test with real OpenCode server across all planned steps (A through G), validating the end-to-end guardrail chain: provider wiring → transport → session creation → plan flow → fail-closed on errors → cleanup.

## Риск-уровень

low (plan-only, controlled environment, no code execution, no deploy/secrets/migrations)

## План

1. **Step A (Pre-check):** Verify clean git state, API health endpoints, port availability, default runtime configuration.
2. **Step B (Start OpenCode):** Launch OpenCode 1.14.33 via npm shim on localhost:4096, verify identity via `/global/health` and `/doc`.
3. **Step C (Runtime override):** Restart API with process-scoped env overrides (`opencode_http`, `4096`, `allow=true`).
4. **Step D (Trigger plan):** Create a task, POST `/runtime/tasks/{id}/plan`, verify session creation, observe message send behavior.
5. **Step F (Post-smoke):** Verify git clean, no file changes, no secret leaks.
6. **Step G (Cleanup):** Stop OpenCode, restart API with default stub settings, verify health.

## Статус

completed

---

## Результаты по шагам

### Step A (Pre-check): ✅ PASS
- Git status clean (no modified/untracked files)
- `GET /health` → 200
- `GET /projects` → 200
- `GET /agents` → 200
- Port 4096 confirmed free
- Defaults confirmed: `RUNTIME_PROVIDER=stub`, `OPENCODE_SERVER_URL=""`, `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=false`, `SANDBOX_RUNNER_MODE=fake`

### Step B (Start OpenCode): ✅ PASS
- OpenCode 1.14.33 started via npm shim: `opencode serve --port 4096 --hostname 127.0.0.1`
- No auth mode (child-process env cleanup of `OPENCODE_SERVER_PASSWORD`/`USERNAME`)
- `GET /global/health` → `{"healthy":true,"version":"1.14.33"}`
- `GET /doc` → OpenAPI 3.1.1 with title "opencode"
- Listener confirmed localhost-only (not 0.0.0.0)

### Step C (Runtime override): ✅ PASS
- API restarted with process-scoped env:
  - `RUNTIME_PROVIDER=opencode_http`
  - `OPENCODE_SERVER_URL=http://127.0.0.1:4096`
  - `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=true`

### Step D (Trigger plan): ✅ PASS (expected integration finding)
- **Task created:** `id=089aa3ca-51a5-450f-881d-88401987bd69`, `external_id=task-0002`, `risk_level=low`
- **Plan triggered:** `POST /runtime/tasks/{id}/plan`
- **Session created:** `session_id=ses_20dd9839affeNEw9pzTOyZOiQY` — proves provider/transport wiring works
- **Message send failed:** `POST /session/{id}/message` returned `400 Bad Request` — payload contract mismatch with OpenCode 1.14.33
- **Fail-closed:** `runtime_error` → `task_failed` (no bypass, no plan saved)
- **Event timeline:** `task_created` → `runtime_error (400)` → `task_failed`

### Step F (Post-smoke): ✅ PASS
- Git status clean
- No file changes detected
- No secret leaks

### Step G (Cleanup): ✅ PASS
- OpenCode process stopped
- API restarted with default stub settings
- Port 4096 confirmed free
- `GET /health` → 200

---

## Изменённые файлы

*Нет.* Код не менялся. Только memory/docs updates.

## Выполненные команды

- `git status` → clean (Steps A, F)
- `curl localhost:8000/health` → 200 (Steps A, C, G)
- `curl localhost:8000/projects` → 200 (Step A)
- `curl localhost:8000/agents` → 200 (Step A)
- `opencode serve --port 4096 --hostname 127.0.0.1` → started (Step B)
- `curl http://127.0.0.1:4096/global/health` → healthy (Step B)
- `curl http://127.0.0.1:4096/doc` → OpenAPI 3.1.1 (Step B)
- `curl -X POST localhost:8000/tasks -d '{...}'` → task created (Step D)
- `curl -X POST localhost:8000/runtime/tasks/{id}/plan` → session created, 400 on message (Step D)
- OpenCode process terminated (Step G)

## Результаты тестов

Не применялось (smoke test, not code change task).

## Diff summary

Нет изменений кода.

## PR

Не создан.

---

## Ключевой результат

**Guardrail chain proven end-to-end:**
1. ✅ Provider wiring (`opencode_http` + `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=true`)
2. ✅ `RealOpenCodeHttpTransport` session creation (`POST /session` → `201`)
3. ✅ Fail-closed on downstream error (`POST /session/{id}/message` → `400` → `runtime_error` → `task_failed`)
4. ✅ No bypass, no silent fallback to stub
5. ✅ No file changes, no secret leaks
6. ✅ Clean startup/shutdown verified

## Интеграционная находка (follow-up BE-07)

`POST /session/{id}/message` returned `400 Bad Request` — payload contract mismatch between backend transport and OpenCode 1.14.33. This is an expected finding for a first real integration test. The fail-closed behavior proved correct: no plan was generated, task transitioned to `task_failed`, no bypass occurred.

**Follow-up task BE-07 needed:** Contract alignment between backend `RealOpenCodeHttpTransport.send_message()` and OpenCode 1.14.33 `/session/{id}/message` payload format.

---

## Риски, возникшие при выполнении

- **Payload contract mismatch (400):** handled gracefully via fail-closed. Task correctly failed without bypass.
- **Port conflict risk:** mitigated by pre-check (Step A) and confirmation (Step G).

## Уроки (Lessons Learned)

1. Real integration testing uncovers contract gaps that unit/mocked tests cannot.
2. The fail-closed chain (`runtime_error` → `task_failed`) works as designed — no silent fallback to stub.
3. Process-scoped env overrides are a safe way to test `opencode_http` without touching `.env`.
4. Port pre-check is essential for controlled smoke tests.

## Следующие шаги

1. **BE-07:** Align `POST /session/{id}/message` payload contract with OpenCode 1.14.33 spec.
2. **BE-07:** Re-run plan step with corrected payload and verify plan generation end-to-end.
3. Memory retrieval tuning: ranking quality + scope heuristics.

---

## Память обновлена
- [x] `.ai_memory/tasks/2026-05-04-task-be06-final-execution.md` (этот файл)
- [x] `.ai_memory/current_state.md`
- [x] `.ai_memory/_INDEX.md`
- [x] `PROJECT_MEMORY.md`
