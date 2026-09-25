#!/usr/bin/env bash
# Start Coach Gary locally with secrets from .env (never committed).
cd "$(dirname "$0")"
set -a; source .env; set +a
exec .venv/bin/python bot.py
