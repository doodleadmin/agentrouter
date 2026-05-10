#!/usr/bin/env bash
# build-miniapp.sh — Build Mini App for production deployment
#
# Usage:
#   ./scripts/build-miniapp.sh
#
# Output: apps/web/dist/ with /app/ base path
#
# This script is LOCAL ONLY. It does NOT deploy, NOT SSH, NOT push.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WEB_DIR="$PROJECT_ROOT/apps/web"

echo "=== Mini App Production Build ==="
echo "Project root: $PROJECT_ROOT"
echo "Web dir:      $WEB_DIR"

# Step 1: Install dependencies
echo ""
echo "[1/3] Installing dependencies..."
cd "$WEB_DIR"
npm ci --prefer-offline

# Step 2: Build with production base path
echo ""
echo "[2/3] Building with VITE_BASE_PATH=/app/ ..."
VITE_BASE_PATH=/app/ npm run build

# Step 3: Verify output
DIST_DIR="$WEB_DIR/dist"
echo ""
echo "[3/3] Verifying output..."
if [ -f "$DIST_DIR/index.html" ]; then
    echo "✅ Build successful"
    echo "   Output: $DIST_DIR"
    echo "   Size:   $(du -sh "$DIST_DIR" | cut -f1)"
    echo ""
    echo "Next steps (manual, controlled deploy):"
    echo "  1. rsync dist/ to /var/www/agentrouter-web/releases/<timestamp>/"
    echo "  2. ln -sfn <release-dir> /var/www/agentrouter-web/current"
    echo "  3. Add Caddyfile.miniapp block and reload Caddy"
    echo "  4. Set TELEGRAM_WEBAPP_URL=https://polyrouter.ru/app/ in .env"
    echo "  5. Restart agentrouter-telegram-bot"
else
    echo "❌ Build failed — dist/index.html not found"
    exit 1
fi
