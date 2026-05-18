#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PYTHON="$ROOT_DIR/.venv/bin/python"
BOOTSTRAP_PYTHON="${BOOTSTRAP_PYTHON:-python3}"
PORT="${PORT:-8501}"
HOST="${HOST:-127.0.0.1}"
REFRESH_DEMO="${REFRESH_DEMO:-0}"
DEMO_SCENARIO="${DEMO_SCENARIO:-bms-fast-charge}"
ALLOW_RUNTIME_INSTALL="${ALLOW_RUNTIME_INSTALL:-0}"

cd "$ROOT_DIR"

if [ ! -x "$DEFAULT_PYTHON" ]; then
  echo "[AVERA] Creating local .venv..."
  "$BOOTSTRAP_PYTHON" -m venv "$ROOT_DIR/.venv"
fi

if [ -n "${PYTHON_BIN:-}" ]; then
  RUNTIME_PYTHON="$PYTHON_BIN"
elif [ -x "$DEFAULT_PYTHON" ]; then
  RUNTIME_PYTHON="$DEFAULT_PYTHON"
else
  RUNTIME_PYTHON="$BOOTSTRAP_PYTHON"
fi

if ! command -v "$RUNTIME_PYTHON" >/dev/null 2>&1; then
  echo "[AVERA] Could not find a usable Python runtime."
  echo "[AVERA] Set PYTHON_BIN=/path/to/python3 and rerun ./start_demo.sh"
  exit 1
fi

PYTHON_VERSION="$("$RUNTIME_PYTHON" - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"

if [[ "$PYTHON_VERSION" == "3.14" ]]; then
  echo "[AVERA] Python 3.14 detected."
  echo "[AVERA] Core CLI and tests are supported, but the Streamlit shell may cold-start slowly in this runtime."
  export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="${PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION:-python}"
fi

if ! "$RUNTIME_PYTHON" - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("streamlit") else 1)
PY
then
  if [ "$ALLOW_RUNTIME_INSTALL" = "1" ] && [ "$RUNTIME_PYTHON" = "$DEFAULT_PYTHON" ]; then
    echo "[AVERA] Installing Streamlit into the project runtime..."
    "$RUNTIME_PYTHON" -m pip install \
      --trusted-host pypi.org \
      --trusted-host files.pythonhosted.org \
      streamlit
  else
    echo "[AVERA] Streamlit is not available in the selected runtime."
    echo "[AVERA] Recommended path:"
    echo "[AVERA]   1. use the project .venv"
    echo "[AVERA]   2. or run: $RUNTIME_PYTHON scripts/runtime_doctor.py"
    echo "[AVERA]   3. or use the static ADAS showcase: docs/AVERA_ADAS_SHOWCASE.html"
    echo "[AVERA] If you intentionally want this launcher to install into the project .venv, rerun with:"
    echo "[AVERA]   ALLOW_RUNTIME_INSTALL=1 ./start_demo.sh"
    exit 1
  fi
fi

if [ "$REFRESH_DEMO" = "1" ]; then
  echo "[AVERA] Refreshing canonical demo artifacts..."
  PYTHONPATH=src "$RUNTIME_PYTHON" -B -m avera demo-refresh \
    --project "fixtures/$DEMO_SCENARIO" \
    --report-out "reports/fixtures/$DEMO_SCENARIO" \
    --memory reports/avera-memory.jsonl \
    --traceability-out reports/avera-traceability-index.json \
    --decision-out reports/avera-decision.json \
    --trend-out reports/avera-trend-index.json \
    --pack-out reports/avera-workspace-pack.json
fi

echo "[AVERA] Starting demo shell..."
echo "[AVERA] Python: $RUNTIME_PYTHON"
echo "[AVERA] Scenario: fixtures/$DEMO_SCENARIO"
echo "[AVERA] Reports: reports/fixtures/$DEMO_SCENARIO"
echo "[AVERA] URL: http://$HOST:$PORT"

PYTHONPATH=src \
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
AVERA_DEFAULT_SCENARIO="$DEMO_SCENARIO" \
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="${PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION:-}" \
"$RUNTIME_PYTHON" -m streamlit run demo/app.py \
  --server.headless true \
  --server.address "$HOST" \
  --server.port "$PORT"
