#!/usr/bin/env bash
# Verification runner: verification/run.sh vl0 | verification/run.sh vl1
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

LEVEL="${1:-vl0}"
CYCLE="${FM_CYCLE:-01_fm_hackrf_rpi5_mvp}"
ITER="${FM_ITER:-1}"
TS="$(date -u +%Y-%m-%d_%H-%M-%S 2>/dev/null || date -u +%Y-%m-%d_%H-%M-%S)"
RUN_ID="${CYCLE}_${ITER}_${TS}"

TELEM_DIR="verification/telemetry/${RUN_ID}"
mkdir -p "$TELEM_DIR"

export FM_HAL=mock
export FM_SOCKET_DIR="/tmp/fm_test_$$"
export FM_DATA_DIR="/tmp/fm_data_$$"
export FM_REPORT_DIR="$FM_DATA_DIR/reports"
export FM_CALIBRATION_DIR="$FM_DATA_DIR/calibration"
mkdir -p "$FM_SOCKET_DIR/progress" "$FM_REPORT_DIR" "$FM_CALIBRATION_DIR"

echo "[run.sh] level=$LEVEL run_id=$RUN_ID"

EXIT_CODE=0
uv run pytest -m "$LEVEL" -v --tb=short 2>&1 | tee "${TELEM_DIR}/pytest_${LEVEL}.txt" || EXIT_CODE=$?

rm -rf "$FM_SOCKET_DIR" "$FM_DATA_DIR" 2>/dev/null || true

echo "[run.sh] run_id=$RUN_ID exit=$EXIT_CODE"
exit $EXIT_CODE
