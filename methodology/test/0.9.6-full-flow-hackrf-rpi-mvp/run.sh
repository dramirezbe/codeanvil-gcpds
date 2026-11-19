#!/usr/bin/env bash
# §0.5 runnable system entry point.
# Usage: ./run.sh [--hal mock]
# Default: the connected HackRF One; pass --hal mock for a local preview.
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
export FM_HAL="${FM_HAL:-real}"

for arg in "$@"; do
  case "$arg" in
    --hal) shift; export FM_HAL="$1"; shift ;;
    --hal=*) export FM_HAL="${arg#--hal=}" ;;
  esac
done

echo "[run.sh] starting FM HackRF RPI5 MVP (HAL=$FM_HAL)"

# Ensure socket and data directories exist
export FM_SOCKET_DIR="${FM_SOCKET_DIR:-/tmp/fm-$$}"
export FM_DATA_DIR="${FM_DATA_DIR:-/tmp/fm-data-$$}"
export FM_REPORT_DIR="${FM_DATA_DIR}/reports"
export FM_CALIBRATION_DIR="${FM_DATA_DIR}/calibration"
mkdir -p "$FM_SOCKET_DIR/progress" "$FM_REPORT_DIR" "$FM_CALIBRATION_DIR"

# Start supervisor (which starts all child subsystems)
uv run fm_supervisor &
SUP_PID=$!

echo "[run.sh] supervisor PID=$SUP_PID"
echo "[run.sh] web UI: http://localhost:8080/spectrum"
echo "[run.sh] press Ctrl-C to stop"

_cleanup() {
  kill "$SUP_PID" 2>/dev/null
  wait "$SUP_PID" 2>/dev/null
  echo "[run.sh] stopped"
  exit 0
}
trap _cleanup INT TERM

wait $SUP_PID
