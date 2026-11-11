#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
level="${1:?Usage: verification/run.sh vl0|vl1}"
case "$level" in vl0|vl1) ;; *) exit 2 ;; esac
mkdir -p verification/telemetry
stamp=$(codeanvil now --machine)
codeanvil telemetry --pid $$ --interval 0.1 --output "verification/telemetry/${level}-${stamp}.jsonl" &
collector=$!
cleanup() {
    kill -TERM "$collector" 2>/dev/null || true
    wait "$collector" 2>/dev/null || true
}
trap cleanup EXIT
uv run --frozen pytest -q -m "$level"
