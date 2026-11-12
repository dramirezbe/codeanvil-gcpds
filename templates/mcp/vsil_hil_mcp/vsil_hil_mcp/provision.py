"""Provisioning script emitted by init_codeanvil (A2 printed-script model).

The MCP never touches the target here: the human reads the script and runs it
once, as root, on the target. Every interpolated value is validated upstream
(config.validate_target_fields, _PUB_RE) and additionally shell-quoted.
"""

import re
import shlex

from .config import Target, release_version

_PUB_RE = re.compile(r"^ssh-ed25519 [A-Za-z0-9+/]+={0,2}( [A-Za-z0-9._@-]+)?$")

_TEMPLATE = r"""#!/usr/bin/env bash
# vsil_hil_mcp provisioning for target "@@NAME@@" (@@HOST@@).
# Run ONCE, as root, ON THE TARGET. Read it first: it creates a user, installs two
# SSH keys with restrictions, and installs CodeAnvil for that user.
set -euo pipefail

HIL_USER=@@USER@@
HIL_WS=@@WS@@
HIL_POLICY=@@POLICY@@
CODEANVIL_VERSION=@@VERSION@@
DEPLOY_PUB=@@DEPLOY_PUB@@
EXEC_PUB=@@EXEC_PUB@@

[ "$(id -u)" -eq 0 ] || { echo "run as root" >&2; exit 1; }

install_pkg() {
  if command -v apt-get >/dev/null 2>&1; then apt-get install -y "$@"
  elif command -v dnf >/dev/null 2>&1; then dnf install -y "$@"
  elif command -v pacman >/dev/null 2>&1; then pacman -S --noconfirm "$@"
  else echo "install $* manually (no known package manager)" >&2; exit 1; fi
}

# 1. unprivileged user + dedicated workspace
id -u "$HIL_USER" >/dev/null 2>&1 || useradd --create-home --shell /bin/bash "$HIL_USER"
HIL_HOME=$(getent passwd "$HIL_USER" | cut -d: -f6)
HIL_GROUP=$(id -gn "$HIL_USER")
install -d -o "$HIL_USER" -g "$HIL_GROUP" -m 0750 "$HIL_WS"

# 2. rrsync (restricted rsync wrapper, ships with rsync)
RRSYNC=$(command -v rrsync || true)
if [ -z "$RRSYNC" ]; then
  command -v rsync >/dev/null 2>&1 || install_pkg rsync
  RRSYNC=$(command -v rrsync || true)
fi
if [ -z "$RRSYNC" ]; then
  for c in /usr/share/doc/rsync/scripts/rrsync /usr/share/doc/rsync/scripts/rrsync.gz /usr/share/doc/rsync/examples/rrsync; do
    if [ -f "$c" ]; then
      case "$c" in *.gz) zcat "$c" > /usr/local/bin/rrsync ;; *) cp "$c" /usr/local/bin/rrsync ;; esac
      chmod 0755 /usr/local/bin/rrsync; RRSYNC=/usr/local/bin/rrsync; break
    fi
  done
fi
[ -n "$RRSYNC" ] || { echo "rrsync not found: install it, then re-run" >&2; exit 1; }

# 3. authorized_keys: deploy key = write-only rsync into the workspace (no shell);
#    exec key = confined unprivileged user (no pty / forwarding via `restrict`).
install -d -o "$HIL_USER" -g "$HIL_GROUP" -m 0700 "$HIL_HOME/.ssh"
AK="$HIL_HOME/.ssh/authorized_keys"
touch "$AK"; chown "$HIL_USER:$HIL_GROUP" "$AK"; chmod 0600 "$AK"
add_key() { grep -qxF -- "$1" "$AK" || printf '%s\n' "$1" >> "$AK"; }
add_key "command=\"$RRSYNC -wo $HIL_WS\",restrict $DEPLOY_PUB"
add_key "restrict $EXEC_PUB"

# 4. policy "trusted": passwordless sudo for the exec user. The host runtime must
#    configure approval for ssh_exec_cmd_trusted. This makes the user root-equivalent:
#    only do it on a lab box you accept is reflashable.
if [ "$HIL_POLICY" = trusted ]; then
  printf 'Grant %s passwordless sudo (root-equivalent)? [y/N] ' "$HIL_USER"
  read -r ans </dev/tty || ans=n
  if [ "$ans" = y ] || [ "$ans" = Y ]; then
    f="/etc/sudoers.d/vsil-hil-$HIL_USER"
    printf '%s ALL=(ALL) NOPASSWD: ALL\n' "$HIL_USER" > "$f.tmp"
    visudo -cf "$f.tmp" >/dev/null && install -m 0440 "$f.tmp" "$f"
    rm -f "$f.tmp"
  fi
fi

# 5. Install the same released CodeAnvil version as the host, as the agent user.
# A release tag is intentional: never install an evolving main branch here.
runuser -u "$HIL_USER" -- env CODEANVIL_VERSION="$CODEANVIL_VERSION" bash -lc '
  set -euo pipefail
  export PATH="$HOME/.local/bin:$PATH"
  command -v uv >/dev/null 2>&1 || { curl -LsSf https://astral.sh/uv/install.sh | sh; }
  uv tool install --force "git+https://github.com/dramirezbe/codeanvil-gcpds.git@v$CODEANVIL_VERSION"
  [ "$(codeanvil --version)" = "codeanvil $CODEANVIL_VERSION" ] || { echo "CodeAnvil version mismatch" >&2; exit 1; }
  codeanvil init
  codeanvil runtime sync'

# 6. project dependencies (needs the code: re-run after the first code_sync if absent)
runuser -u "$HIL_USER" -- env HIL_WS="$HIL_WS" bash -lc '
  export PATH="$HOME/.local/bin:$PATH"; cd "$HIL_WS"
  if [ -f pyproject.toml ]; then uv sync --frozen --no-dev; else echo "no pyproject.toml yet: run code_sync, then: cd $HIL_WS && uv sync --frozen --no-dev"; fi'

# 7. host key: compare with what the first ssh from the host recorded (TOFU)
echo "SSH host key fingerprint of this machine:"
for k in /etc/ssh/ssh_host_*_key.pub; do ssh-keygen -lf "$k"; done
echo "Provisioning done. OS packages / udev rules (SDR drivers, plugdev) are NOT installed:"
echo "do them through ssh_exec_cmd_trusted so you approve each command."
"""


def _pub(pub_text: str) -> str:
    line = pub_text.strip()
    if "\n" in line or not _PUB_RE.match(line):
        raise ValueError("unexpected public key format")
    return line


def render_script(target: Target, deploy_pub: str, exec_pub: str, codeanvil_version: str) -> str:
    subs = {
        "@@NAME@@": target.name,  # validated, comment line only
        "@@HOST@@": target.host,
        "@@USER@@": shlex.quote(target.user),
        "@@WS@@": shlex.quote(target.workspace),
        "@@POLICY@@": shlex.quote(target.hil_policy),
        "@@DEPLOY_PUB@@": shlex.quote(_pub(deploy_pub)),
        "@@EXEC_PUB@@": shlex.quote(_pub(exec_pub)),
        "@@VERSION@@": shlex.quote(release_version(codeanvil_version)),
    }
    out = _TEMPLATE
    for k, v in subs.items():
        out = out.replace(k, v)
    return out
