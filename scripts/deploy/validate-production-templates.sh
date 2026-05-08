#!/usr/bin/env bash
# validate-production-templates.sh — Safety checks for production config files
#
# Usage: bash scripts/deploy/validate-production-templates.sh
#
# This script:
#   - Does NOT require root
#   - Does NOT install anything
#   - Does NOT read actual .env values
#   - Only checks template files for safety violations
#
# Exit code 0 = all checks passed, 1 = one or more failures.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FAIL=0

check() { echo -n "  CHECK: $1 ... "; }
pass()  { echo "PASS"; }
fail()  { echo "FAIL: $1"; FAIL=1; }

echo "=== Production Template Validation ==="
echo ""

# ---- 1. Required files exist ----
echo "1. Required files exist"
for f in \
    infra/deploy/Caddyfile \
    infra/deploy/agentrouter-api.service \
    infra/deploy/agentrouter-worker.service \
    infra/deploy/agentrouter-telegram-bot.service \
    infra/docker/docker-compose.prod.yml \
    .env.example \
    scripts/deploy/preflight.sh \
    scripts/deploy/release.sh \
    scripts/deploy/rollback.sh \
    scripts/deploy/smoke.sh \
; do
    check "$f"
    if [[ -f "$REPO_ROOT/$f" ]]; then pass; else fail "missing"; fi
done

# ---- 2. No real-looking Telegram tokens ----
echo ""
echo "2. No real secrets in templates"
for f in infra/deploy/Caddyfile infra/deploy/*.service infra/docker/docker-compose.prod.yml .env.example; do
    check "$(basename $f) has no real bot token"
    if grep -qP '\d{8,11}:[\w\-]{30,45}' "$REPO_ROOT/$f" 2>/dev/null; then
        fail "found real-looking Telegram bot token"
    else pass; fi
done

# ---- 3. No SQL_ECHO=true defaults ----
echo ""
echo "3. No SQL_ECHO=true defaults"
for f in infra/deploy/*.service infra/docker/docker-compose.prod.yml .env.example; do
    check "$(basename $f) no SQL_ECHO=true"
    if grep -q 'SQL_ECHO=true' "$REPO_ROOT/$f" 2>/dev/null; then
        fail "found SQL_ECHO=true"
    else pass; fi
done

# ---- 4. No DEBUG=true in production templates ----
echo ""
echo "4. No DEBUG=true defaults"
for f in infra/deploy/*.service infra/docker/docker-compose.prod.yml; do
    check "$(basename $f) no DEBUG=true"
    if grep -q 'DEBUG=true' "$REPO_ROOT/$f" 2>/dev/null; then
        fail "found DEBUG=true"
    else pass; fi
done

# ---- 5. API binds 127.0.0.1 in systemd ----
echo ""
echo "5. API systemd binds 127.0.0.1"
check "agentrouter-api.service uses 127.0.0.1"
if grep -q '0\.0\.0\.0' "$REPO_ROOT/infra/deploy/agentrouter-api.service" 2>/dev/null; then
    fail "found 0.0.0.0 bind"
elif grep -q '127\.0\.0\.1' "$REPO_ROOT/infra/deploy/agentrouter-api.service" 2>/dev/null; then
    pass
else fail "no bind address found"; fi

# ---- 6. No inline secrets in systemd units ----
echo ""
echo "6. No inline secrets in systemd units"
for f in infra/deploy/*.service; do
    check "$(basename $f) no inline secrets"
    if grep -qiP '(password|secret|token)=' "$REPO_ROOT/$f" 2>/dev/null; then
        fail "found inline secret assignment"
    else pass; fi
done

# ---- 7. Deploy scripts safety defaults ----
echo ""
echo "7. Deploy scripts safety defaults"
for f in scripts/deploy/preflight.sh scripts/deploy/release.sh scripts/deploy/rollback.sh scripts/deploy/smoke.sh; do
    check "$(basename $f) defines DRY_RUN default"
    if grep -q 'DRY_RUN="${DRY_RUN:-true}"' "$REPO_ROOT/$f" 2>/dev/null; then
        pass
    else
        fail "missing DRY_RUN safe default"
    fi
done

check "preflight blocks .env/.env.local"
if grep -q 'refusing to run against' "$REPO_ROOT/scripts/deploy/preflight.sh" 2>/dev/null; then
    pass
else
    fail "preflight .env/.env.local block not found"
fi

check "deploy scripts do not cat .env"
if grep -qE 'cat\s+.*\.env' "$REPO_ROOT/scripts/deploy/preflight.sh" "$REPO_ROOT/scripts/deploy/release.sh" "$REPO_ROOT/scripts/deploy/rollback.sh" "$REPO_ROOT/scripts/deploy/smoke.sh" 2>/dev/null; then
    fail "found forbidden 'cat .env' usage"
else
    pass
fi

check "release has CONFIRM_PRODUCTION_DEPLOY"
if grep -q 'CONFIRM_PRODUCTION_DEPLOY' "$REPO_ROOT/scripts/deploy/release.sh" 2>/dev/null; then pass; else fail "missing CONFIRM_PRODUCTION_DEPLOY"; fi

check "release has CONFIRM_MIGRATIONS"
if grep -q 'CONFIRM_MIGRATIONS' "$REPO_ROOT/scripts/deploy/release.sh" 2>/dev/null; then pass; else fail "missing CONFIRM_MIGRATIONS"; fi

check "release has CONFIRM_SERVICE_RESTART"
if grep -q 'CONFIRM_SERVICE_RESTART' "$REPO_ROOT/scripts/deploy/release.sh" 2>/dev/null; then pass; else fail "missing CONFIRM_SERVICE_RESTART"; fi

check "rollback has CONFIRM_ROLLBACK"
if grep -q 'CONFIRM_ROLLBACK' "$REPO_ROOT/scripts/deploy/rollback.sh" 2>/dev/null; then pass; else fail "missing CONFIRM_ROLLBACK"; fi

check "rollback has CONFIRM_DB_ROLLBACK"
if grep -q 'CONFIRM_DB_ROLLBACK' "$REPO_ROOT/scripts/deploy/rollback.sh" 2>/dev/null; then pass; else fail "missing CONFIRM_DB_ROLLBACK"; fi

check "smoke has no Telegram live actions"
if grep -qiE 'sendMessage|botfather|telegram\.org|start_polling|python -m app\.main' "$REPO_ROOT/scripts/deploy/smoke.sh" 2>/dev/null; then
    fail "smoke script appears to perform Telegram live actions"
else
    pass
fi

check "deploy scripts contain no SQL_ECHO=true"
if grep -q 'SQL_ECHO=true' "$REPO_ROOT/scripts/deploy/preflight.sh" "$REPO_ROOT/scripts/deploy/release.sh" "$REPO_ROOT/scripts/deploy/rollback.sh" "$REPO_ROOT/scripts/deploy/smoke.sh" 2>/dev/null; then
    fail "found SQL_ECHO=true in deploy scripts"
else
    pass
fi

check "deploy scripts contain no DEBUG=true"
if grep -q 'DEBUG=true' "$REPO_ROOT/scripts/deploy/preflight.sh" "$REPO_ROOT/scripts/deploy/release.sh" "$REPO_ROOT/scripts/deploy/rollback.sh" "$REPO_ROOT/scripts/deploy/smoke.sh" 2>/dev/null; then
    fail "found DEBUG=true in deploy scripts"
else
    pass
fi

# ---- 8. Syntax check deploy scripts ----
echo ""
echo "8. Syntax check deploy scripts"
for f in \
    scripts/deploy/validate-production-templates.sh \
    scripts/deploy/preflight.sh \
    scripts/deploy/release.sh \
    scripts/deploy/rollback.sh \
    scripts/deploy/smoke.sh \
; do
    check "bash -n $(basename $f)"
    if bash -n "$REPO_ROOT/$f" 2>/dev/null; then
        pass
    else
        fail "syntax error"
    fi
done

# ---- 9. systemd-analyze (if available) ----
echo ""
echo "9. systemd unit validation (if systemd-analyze available)"
if command -v systemd-analyze &>/dev/null; then
    for f in infra/deploy/*.service; do
        check "systemd-analyze verify $(basename $f)"
        if systemd-analyze verify "$REPO_ROOT/$f" 2>/dev/null; then
            pass
        else echo "SKIP (systemd-analyze verify failed — OK on non-systemd hosts)"; fi
    done
else
    echo "  SKIP: systemd-analyze not available"
fi

# ---- 10. docker compose config check (if available) ----
echo ""
echo "10. Docker Compose config check (if docker compose available)"
if command -v docker &>/dev/null && docker compose version &>/dev/null; then
    check "docker compose config on prod compose"
    if docker compose -f "$REPO_ROOT/infra/docker/docker-compose.prod.yml" config --quiet 2>/dev/null; then
        pass
    else echo "SKIP (docker compose config needs .env with required vars)"; fi
else
    echo "  SKIP: docker compose not available"
fi

echo ""
echo "=== Result ==="
if [[ $FAIL -eq 0 ]]; then
    echo "ALL CHECKS PASSED"
    exit 0
else
    echo "SOME CHECKS FAILED"
    exit 1
fi
