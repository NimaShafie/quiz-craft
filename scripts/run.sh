#!/usr/bin/env bash
# QuizCraft — local dev launcher
# Usage:
#   ./scripts/run.sh                    # self-hosted mode (port 8501)
#   HOSTED_MODE=true ./scripts/run.sh   # hosted/rate-limited mode (port 8502)
#
# Ollama runs on the dedicated AI VM at 10.0.0.12 — not locally.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$ROOT/.venv"
OLLAMA_HOST="${OLLAMA_HOST:-http://10.0.0.12:11434}"
PORT=8501
[ "${HOSTED_MODE:-false}" = "true" ] && PORT=8502

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[run.sh]${NC} $*"; }
warn()  { echo -e "${YELLOW}[run.sh]${NC} $*"; }
error() { echo -e "${RED}[run.sh]${NC} $*" >&2; exit 1; }

# ── Python ───────────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  error "python3 not found. Install Python 3.11+ from https://python.org"
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
  error "Python 3.11+ required (found $PYTHON_VERSION)"
fi
info "Python $PYTHON_VERSION OK"

# ── Virtual environment ───────────────────────────────────────────────────────
if [ ! -d "$VENV" ]; then
  info "Creating virtual environment at .venv ..."
  python3 -m venv "$VENV"
fi

# Windows (Git Bash / MINGW) uses Scripts/, Unix uses bin/
if [ -f "$VENV/Scripts/activate" ]; then
  ACTIVATE="$VENV/Scripts/activate"
else
  ACTIVATE="$VENV/bin/activate"
fi

# shellcheck source=/dev/null
source "$ACTIVATE"
info "Venv activated"

# ── Upgrade pip + dependencies ────────────────────────────────────────────────
info "Upgrading pip ..."
python -m pip install --upgrade pip --no-cache-dir --quiet

info "Installing/upgrading Python dependencies ..."
pip install --upgrade --no-cache-dir -r "$ROOT/requirements.txt" --quiet
info "Dependencies up to date"

# ── Remote Ollama reachability check ─────────────────────────────────────────
info "Checking Ollama at $OLLAMA_HOST ..."
if ! curl -sf --connect-timeout 5 "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; then
  error "Cannot reach Ollama at $OLLAMA_HOST — is the AI VM (10.0.0.12) up and is Ollama running?"
fi
info "Ollama reachable at $OLLAMA_HOST"

# ── Launch QuizCraft ──────────────────────────────────────────────────────────
info "Starting QuizCraft on http://localhost:$PORT  (HOSTED_MODE=${HOSTED_MODE:-false})"
export OLLAMA_HOST
cd "$ROOT"
exec streamlit run src/quiz_craft.py \
  --server.port="$PORT" \
  --server.address=127.0.0.1 \
  --browser.gatherUsageStats=false
