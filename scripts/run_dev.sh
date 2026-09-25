#!/usr/bin/env bash
set -e

echo ">>> Starting Enermax CRM Local Development Services..."

# Activate backend virtualenv and run in background
cd "$(dirname "$0")/../backend"
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo ">>> Backend running under PID ${BACKEND_PID}"

# Run frontend in foreground
cd ../frontend
npm run dev

# Cleanup on exit
kill $BACKEND_PID
