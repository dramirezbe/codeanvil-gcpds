#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
acceptance=odd/tasks/codeanvil-ui-v4/acceptance
python=${CODEANVIL_ACCEPTANCE_PYTHON:-.venv/bin/python}
fixture=$(mktemp -d)
echo "Fixture: $fixture"
servers=()
cleanup() {
  for pid in "${servers[@]}"; do kill "$pid" 2>/dev/null || true; done
  for pid in "${servers[@]}"; do wait "$pid" 2>/dev/null || true; done
}
trap cleanup EXIT

"$python" "$acceptance/fixture.py" "$fixture"
ports=("${CODEANVIL_ARCHIVE_PORT:-18763}" "${CODEANVIL_FIXTURE_PORT:-18764}")
projects=(methodology/test/0.9.6-full-flow-hackrf-rpi-mvp "$fixture")
for index in 0 1; do
  "$python" -c 'import sys
from pathlib import Path
import uvicorn
from codeanvil.UI.ui import create_app
uvicorn.run(create_app(Path(sys.argv[1])), host="127.0.0.1", port=int(sys.argv[2]), access_log=False)
' "${projects[$index]}" "${ports[$index]}" &
  servers+=("$!")
done
for index in 0 1; do
  for attempt in {1..25}; do
    kill -0 "${servers[$index]}"
    if curl -fsS "http://127.0.0.1:${ports[$index]}/api/context" >/dev/null 2>&1; then break; fi
    sleep 0.2
  done
done
node "$acceptance/workspace.cjs" "http://127.0.0.1:${ports[0]}" "http://127.0.0.1:${ports[1]}"
