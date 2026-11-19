#!/usr/bin/env bash
# Run on the Pi as the user that has access to the HackRF.
# Optional: FM_WEB_PORT=24000 ./install-service.sh
set -euo pipefail

service=v0.9.6-vsil-v4-fm-hackrf-rpi.service
directory=v0.9.6-vsil-v4-fm-hackrf-rpi
unit_path="/etc/systemd/system/$service"
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
export PATH="$HOME/.local/bin:$PATH"

if (( EUID == 0 )); then
  echo "Run this script as the HackRF user. The installer uses sudo for systemd." >&2
  exit 1
fi

for tool in uv node pnpm python3 curl sudo systemctl; do
  if ! command -v "$tool" >/dev/null; then
    echo "Required command unavailable: $tool" >&2
    exit 1
  fi
done

node_dir=$(dirname -- "$(command -v node)")
pnpm_dir=$(dirname -- "$(command -v pnpm)")
service_path="$node_dir:$pnpm_dir:/usr/local/bin:/usr/bin:/bin"
# These values are embedded in systemd directives. Reject directive metacharacters.
for value in "$project_dir" "$service_path"; do
  if [[ ! "$value" =~ ^[a-zA-Z0-9_./:+@-]+$ ]]; then
    echo "Unsupported project or tool path: $value" >&2
    exit 1
  fi
done

sudo -v
existing_port=""
if [[ -r "$unit_path" ]]; then
  existing_port=$(sed -n 's/^Environment=FM_WEB_PORT=//p' "$unit_path")
fi
requested_port=${FM_WEB_PORT:-$existing_port}
port=$(python3 - "$requested_port" "$existing_port" <<'PY'
import random
import socket
import sys

requested, existing = sys.argv[1:]
if requested and (not requested.isascii() or not requested.isdecimal()
                  or len(requested) > 5 or not 1024 <= int(requested) <= 65535):
    sys.exit("FM_WEB_PORT must be an integer between 1024 and 65535")

if requested and requested == existing:
    print(requested)
else:
    candidates = [int(requested)] if requested else random.sample(range(20000, 30000), 128)
    for candidate in candidates:
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as listener:
            listener.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            try:
                listener.bind(("::", candidate))
            except OSError:
                continue
        print(candidate)
        break
    else:
        sys.exit("Could not find a free web port")
PY
)

cd -- "$project_dir"
uv sync --locked --no-dev
uv pip install --python .venv/bin/python ntplib==0.4.0
pnpm --filter fm_web install --frozen-lockfile

unit=$(mktemp)
trap 'unlink "$unit"' EXIT
cat > "$unit" <<UNIT
[Unit]
Description=FM spectrum monitor for HackRF One on Raspberry Pi
After=network.target

[Service]
Type=simple
User=$(id -un)
WorkingDirectory=$project_dir
RuntimeDirectory=$directory
StateDirectory=$directory
RuntimeDirectoryMode=0750
StateDirectoryMode=0750
Environment=PATH=$service_path
Environment=FM_HAL=real
Environment=FM_WEB_PORT=$port
Environment=FM_SOCKET_DIR=/run/$directory
Environment=FM_DATA_DIR=/var/lib/$directory
Environment=FM_REPORT_DIR=/var/lib/$directory/reports
Environment=FM_CALIBRATION_DIR=/var/lib/$directory/calibration
ExecStartPre=/usr/bin/mkdir -p /var/lib/$directory/reports /var/lib/$directory/calibration
ExecStart=$project_dir/.venv/bin/python -m fm_supervisor
KillMode=control-group
TimeoutStopSec=15
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

sudo install -m 0644 "$unit" "$unit_path"
sudo systemctl daemon-reload
sudo systemctl enable "$service"
sudo systemctl restart "$service"

url="http://127.0.0.1:$port"
for (( attempt = 0; attempt < 30; attempt++ )); do
  if curl -fsS --max-time 2 "$url/api/spectrum" 2>/dev/null | python3 -c '
import json
import sys
try:
    data = json.load(sys.stdin)
except ValueError:
    sys.exit(1)
sys.exit(not (data.get("hal") == "real" and data.get("data_state") == "ok"))
'; then
    printf 'Started %s with live HackRF data. Spectrum: %s/spectrum\n' "$service" "$url"
    exit 0
  fi
  sleep 1
done
echo "The service did not produce a complete HackRF sweep. Inspect: journalctl -u $service -n 50" >&2
exit 1
