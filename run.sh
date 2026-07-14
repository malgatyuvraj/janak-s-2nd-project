#!/usr/bin/env bash
# Start backend + frontend for local development.
# Backend on :8000, frontend on :5173.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

# ---- backend ----
cd "$ROOT/backend"
if [ ! -d venv ]; then
  python3.13 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install -q -r requirements.txt
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 \
  > /tmp/ats_backend.log 2>&1 &
disown || true
echo "backend:  http://127.0.0.1:8000  (logs: /tmp/ats_backend.log)"

# ---- frontend ----
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then
  npm install
fi
nohup npm run dev > /tmp/ats_frontend.log 2>&1 &
disown || true
echo "frontend: http://127.0.0.1:5173  (logs: /tmp/ats_frontend.log)"

echo "open http://127.0.0.1:5173 in your browser"
