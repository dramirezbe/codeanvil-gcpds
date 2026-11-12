#!/usr/bin/env bash
# Compatibility entry point. Equipment identity/key custody lives in the CLI.
# Run inside the project: setup_credentials_ssh_hil.sh -u pi -i raspberry.local
set -euo pipefail
exec codeanvil credential-setup "$@"
