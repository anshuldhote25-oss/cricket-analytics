#!/bin/bash
# ============================================================
# start.sh — Start the Cricket Analytics AI Agent
# Run from the cricket-analytics/ folder: bash start.sh
# ============================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo ""
echo "=============================================="
echo "  Cricket Analytics AI Agent — Startup"
echo "=============================================="

# Check .env exists
if [ ! -f .env ]; then
  echo "  [ERROR] .env file not found. Copy .env.example to .env and fill in your credentials."
  exit 1
fi

# Check database is reachable
echo ""
echo "  Checking database..."
python3 -c "from database import test_connection; exit(0 if test_connection() else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "  [ERROR] Cannot connect to PostgreSQL. Make sure it is running."
  exit 1
fi
echo "  Database: connected"

# Build frontend if static/ doesn't exist or is older than src/
echo ""
echo "  Checking frontend build..."
if [ ! -d "static" ] || [ "frontend/src/App.jsx" -nt "static/index.html" ]; then
  echo "  Building React frontend..."
  cd frontend && npm run build && cd ..
  echo "  Frontend: built"
else
  echo "  Frontend: up to date"
fi

# Start Nginx
echo ""
echo "  Starting Nginx..."
sudo nginx -t 2>/dev/null && sudo nginx 2>/dev/null || sudo nginx -s reload 2>/dev/null
echo "  Nginx: running on https://localhost"

# Start FastAPI
echo ""
echo "=============================================="
echo "  Starting FastAPI backend..."
echo "  Local:  https://localhost"
echo "  API:    http://localhost:8000"
echo ""
echo "  To expose publicly, run in another terminal:"
echo "  ngrok http 8000"
echo "=============================================="
echo ""

uvicorn web_app:app --host 127.0.0.1 --port 8000
