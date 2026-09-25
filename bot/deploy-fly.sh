#!/usr/bin/env bash
# Deploy Coach Carter to Fly.io: one shared-cpu-1x / 256MB machine (~$1.94/mo) + 1GB volume for SQLite.
# Usage: ./deploy-fly.sh [app-name]      secrets are read from ./.env (TELEGRAM_TOKEN, FLYMYAI_API_KEY)
set -euo pipefail
cd "$(dirname "$0")"
APP="${1:-coach-carter-bot}"
REGION="${REGION:-iad}"

command -v fly >/dev/null || { echo "flyctl missing: curl -L https://fly.io/install.sh | sh"; exit 1; }
fly auth whoami >/dev/null 2>&1 || fly auth login
[ -f .env ] || { echo "Create .env from .env.example first"; exit 1; }

# Telegram hands updates to exactly one poller per token.
if pgrep -f "\.venv/bin/python bot.py" >/dev/null; then
  echo "Stopping the local bot so Fly.io becomes the only poller"
  pkill -f "\.venv/bin/python bot.py" || true
fi

sed -i "s/^app = .*/app = \"$APP\"/" fly.toml
fly apps create "$APP" >/dev/null 2>&1 || echo "App $APP already exists"
fly volumes list -a "$APP" 2>/dev/null | grep -q gary_data \
  || fly volumes create gary_data --size 1 --region "$REGION" -a "$APP" --yes
grep -E '^(TELEGRAM_TOKEN|FLYMYAI_API_KEY)=' .env | fly secrets import -a "$APP" --stage
fly deploy -a "$APP" --ha=false
fly scale count 1 -a "$APP" --yes
echo "Coach Carter is live on Fly.io. Logs: fly logs -a $APP"
