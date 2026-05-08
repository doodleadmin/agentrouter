# Task: SEC-03 Phase 2 — Centralized Secrets Redaction

**Date:** 2026-05-08
**Agent:** security-engineer
**Status:** completed
**Risk level:** medium (cross-component refactoring, 4 subsystems affected)

## Goal

Create a centralized secrets redaction module that unifies 4 previously separate redaction systems into a single source of truth. The module must cover all known secret patterns in the codebase and be imported by all subsystems that handle potentially sensitive data.

## What was done

### Central module: `apps/api/app/security/redaction.py`

Created a single `redaction.py` with 5 public functions:

| Function | Purpose |
|----------|---------|
| `redact_text(text: str) -> str` | Redact secrets in plain text, replacing matches with `[REDACTED:TYPE]` |
| `redact_mapping(data: dict) -> dict` | Deep-redact all string values in a nested dict |
| `contains_secret(text: str) -> bool` | Fast check: does text contain any known secret pattern? |
| `sanitize_metadata(metadata: dict) -> dict` | Remove sensitive keys + redact values |
| `find_secret_matches(text: str) -> list` | Return list of (pattern_name, match) tuples (for debugging/audit) |

### 10 secret pattern types covered

| # | Pattern | Regex | Marker |
|---|---------|-------|--------|
| 1 | Telegram bot token | `\d{9,10}:[\w-]{35,}` | `[REDACTED:TELEGRAM_TOKEN]` |
| 2 | Bearer token | `Bearer\s+[\w\-\.=\+]+` | `[REDACTED:BEARER]` |
| 3 | JWT | `eyJ[\w\-]+\.[\w\-]+\.[\w\-]+` | `[REDACTED:JWT]` |
| 4 | OpenAI/sk- API key | `sk-[\w]{20,}` | `[REDACTED:API_KEY]` |
| 5 | GitHub personal access token | `gh[pousr]_[\w]{20,}` | `[REDACTED:GITHUB_TOKEN]` |
| 6 | DB password in URL | `(?<=://[^:]+:)[^@]+(?=@)` | `[REDACTED:DB_PASSWORD]` |
| 7 | Redis password | `(?<=://)[^:@]+(?=@)` (Redis URL) | `[REDACTED:REDIS_PASSWORD]` |
| 8 | Generic password/secret assignment | `(password|secret|token|key|passwd)\s*[:=]\s*[\S]+` | `[REDACTED:<TYPE>]` |
| 9 | PEM private key | `-----BEGIN[\w\s]+PRIVATE KEY-----` block | `[REDACTED:PEM_KEY]` |
| 10 | CALLBACK_SECRET | `(CALLBACK_SECRET|callback_secret)\s*[:=]\s*\S+` | `[REDACTED:CALLBACK_SECRET]` |

### Subsystem unification

Four previously separate redaction implementations unified:

1. **Audit service** (`audit_service.py`): Removed local `redact_text()` (regex-based, 5 patterns) and `sanitize_metadata()`. Now imports from `app.security.redaction`. Net change: −70 lines.

2. **Runtime guardrails** (`runtime_guardrails.py`): `redact_payload()` now delegates to `redact_mapping()`. `redact_text()` import from central.

3. **Task events** (`task_event_service.py`): `TaskEventService.create()` now applies `redact_mapping(payload)` before INSERT, using the central `redaction` module.

4. **Worker redaction** (`worker/app/services/redaction.py`): Pattern set synced to match the 10 central patterns. Added sync comment referencing `apps.api.app.security.redaction` as source of truth.

5. **Worker agent_plan** (`worker/app/tasks/agent_plan.py`): `redact_text()` applied before exception logging to prevent secret leakage in worker stderr.

### Out of scope (deliberately not changed)

- **MemoryPolicyService**: Keeps its REJECT behavior for writes containing detected secrets (different semantics than redaction).
- **Pre-commit hooks**: Not added (deferred to Phase 3).
- **Git history scan**: Not performed (no secret-commits detected in this task).
- **API logging filter (uvicorn)**: Not changed (telegram-bot has its own SecretRedactionFilter from TG-04).
- **.env/secrets**: Not touched.

## Changed files (12)

### NEW (2)
- `apps/api/app/security/redaction.py` — Central redaction module (5 functions, 10 patterns)
- `apps/api/tests/test_security_redaction.py` — 46 unit tests

### MODIFIED (10)
- `apps/api/app/security/__init__.py` — Export redaction functions
- `apps/api/app/services/audit_service.py` — Removed local redact_text/sanitize_metadata, imports central (−70 lines)
- `apps/api/app/policy/runtime_guardrails.py` — redact_payload delegates to redact_mapping
- `apps/api/app/services/task_event_service.py` — Payload redaction before INSERT
- `apps/worker/app/services/redaction.py` — Synced 10-pattern set with sync comment
- `apps/worker/app/tasks/agent_plan.py` — redact_text() before exception logging
- `apps/api/tests/test_security_audit.py` — 3 assertions updated
- `apps/api/tests/test_runtime_be04.py` — 1 assertion updated
- `apps/worker/tests/test_execute_security.py` — 1 assertion updated
- `apps/worker/tests/test_execute_e2e_fake.py` — 1 assertion updated

## Validation

| Component | Tests | Delta |
|-----------|-------|-------|
| API | 393/393 | +46 (was 347) |
| Telegram-bot | 79/79 | 0 |
| Worker | 98/98 | 0 |
| **Total** | **570/570** | **+46** |

- ruff: clean (all 3 packages)
- compileall: clean (all 3 packages)

## Result

✅ Centralized secrets redaction module created and wired into all 4 subsystems. 10 pattern types covered. 46 new tests. All existing tests pass. No regressions. No secrets exposed.

## Open questions

None.

## Follow-up tasks

- SEC-03 Phase 3: pre-commit hook to scan staged files for secrets before commit
- SEC-03 Phase 4: Git history scan for previously-committed secrets
- Consider adding uvicorn logging filter for API (similar to Telegram-bot SecretRedactionFilter from TG-04)

## Memory checkpoint

- **Memory updated:** yes
- **Files updated:** PROJECT_MEMORY.md, .ai_memory/current_state.md, .ai_memory/_INDEX.md, .ai_memory/tasks/2026-05-08-task-sec03-secrets-redaction.md (NEW)
- **Commit hash:** (pending)
- **Skipped reason:** N/A
