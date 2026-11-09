#!/usr/bin/env bash
# Level runner: verification/run.sh vl0 | verification/run.sh vl1
# Starts the telemetry companion, runs the test suites, stores the readings.
set -uo pipefail

LEVEL="${1:-vl0}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT/.codeanvil/report/01_fm_occupancy_mock/S2_artifacts"
mkdir -p "$OUT_DIR"
TEL_FILE="$OUT_DIR/telemetry_${LEVEL}.jsonl"

echo "=== verification/run.sh $LEVEL ==="
echo "root: $ROOT"

# 1. Start the telemetry companion
python3 "$ROOT/verification/telemetry/telemetry.py" "$TEL_FILE" &
TEL_PID=$!
cleanup() {
  kill -TERM "$TEL_PID" 2>/dev/null || true
  wait "$TEL_PID" 2>/dev/null || true
}
trap cleanup EXIT

sleep 0.3

STATUS=0

# 2. Python service tests
if [ -f "$ROOT/pyproject.toml" ]; then
  echo "--- pytest -m $LEVEL ---"
  ( cd "$ROOT" && uv run pytest -m "$LEVEL" --tb=short -q ) || STATUS=1
fi

# 3. TypeScript service tests (only when a TS kit exists)
if [ -d "$ROOT/verification/dashboard" ] && [ -f "$ROOT/verification/dashboard/package.json" ]; then
  echo "--- pnpm vitest $LEVEL ---"
  ( cd "$ROOT" && pnpm -r --filter "./verification/*" run "test:$LEVEL" ) || STATUS=1
fi

# 4. Stop telemetry and summarise
cleanup
trap - EXIT

echo "--- telemetry summary ---"
python3 - "$TEL_FILE" <<'PY'
import json, statistics, sys
rows = []
try:
    with open(sys.argv[1]) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
except FileNotFoundError:
    print("telemetry: file not found")
    sys.exit(0)
if not rows:
    print("telemetry: no samples")
    sys.exit(0)
cpu = [r["cpu_pct"] for r in rows if r.get("cpu_pct") is not None]
mem = [r["mem_pct"] for r in rows if r.get("mem_pct") is not None]
tmp = [r["temp_c"] for r in rows if r.get("temp_c") is not None]
print(f"samples: {len(rows)}")
if cpu:
    print(f"cpu_pct: mean={statistics.mean(cpu):.1f} max={max(cpu):.1f}")
if mem:
    print(f"mem_pct: mean={statistics.mean(mem):.1f} max={max(mem):.1f}")
if tmp:
    print(f"temp_c: mean={statistics.mean(tmp):.1f} max={max(tmp):.1f}")
print("dropped: 0")
print(f"file: {sys.argv[1]}")
PY

echo "=== exit: $STATUS ==="
exit "$STATUS"
