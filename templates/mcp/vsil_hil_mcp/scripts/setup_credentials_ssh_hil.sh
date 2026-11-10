#!/usr/bin/env bash
# setup_credentials_ssh_hil.sh — run on the HOST (your control PC).
#
# Bootstraps an HIL target's agent credentials over SSH, using the target's
# EXISTING admin login (password). It generates the vsil_hil_mcp confined keys
# (if absent) and, on the target, creates a login-locked agent user with NOPASSWD
# sudo + a workspace, installs rrsync, and installs the agent's two public keys
# (deploy = write-only rsync via rrsync; exec = command key).
#
# It NEVER touches your personal SSH credentials: your ~/.ssh keys, agent,
# config and known_hosts are not read or modified. The password is used only for
# this one bootstrap connection; the agent then authenticates with its own keys.
#
# The agent user gets NOPASSWD sudo (root-equivalent) — only run this against a
# lab machine you own and can reflash (this matches the MCP `trusted` policy).
set -euo pipefail

ADMIN_USER=""; ADMIN_PASS="${CODEANVIL_HIL_PASSWORD:-}"; TARGET_IP=""; PORT=22
AGENT_USER="codeanvil"; TARGET_NAME=""; WORKSPACE=""

usage() {
  cat >&2 <<USAGE
Usage: $0 -u <admin_user> [-p <admin_password>] -i <target_ip> [options]

  -u, --user         existing admin/login user on the target (bootstrap only)
  -p, --password     that user's password (used only for this bootstrap SSH).
                     Prefer the env var CODEANVIL_HIL_PASSWORD (not visible in ps);
                     -p is the fallback when the variable is unset.
  -i, --ip           target IP or hostname
  -P, --port         SSH port (default: 22)
  -a, --agent-user   agent user to create on the target (default: codeanvil)
  -t, --target       MCP target name / key-store dir (default: derived from the IP)
  -w, --workspace    agent workspace on the target (default: /home/<agent>/workspace)
  -h, --help

Your own ~/.ssh keys, agent, config and known_hosts are never used or modified.
USAGE
  exit "${1:-2}"
}

while [ $# -gt 0 ]; do
  case "$1" in
    -u|--user)        ADMIN_USER="${2:-}"; shift 2;;
    -p|--password)    ADMIN_PASS="${2:-}"; shift 2;;
    -i|--ip)          TARGET_IP="${2:-}"; shift 2;;
    -P|--port)        PORT="${2:-}"; shift 2;;
    -a|--agent-user)  AGENT_USER="${2:-}"; shift 2;;
    -t|--target)      TARGET_NAME="${2:-}"; shift 2;;
    -w|--workspace)   WORKSPACE="${2:-}"; shift 2;;
    -h|--help)        usage 0;;
    *) echo "unknown argument: $1" >&2; usage;;
  esac
done

[ -n "$ADMIN_USER" ] && [ -n "$ADMIN_PASS" ] && [ -n "$TARGET_IP" ] || usage
TARGET_NAME="${TARGET_NAME:-${TARGET_IP//[.:]/_}}"
WORKSPACE="${WORKSPACE:-/home/$AGENT_USER/workspace}"

# Mirror the MCP's strict allowlists (these values reach ssh/rsync and a root shell).
grep -qE '^[a-z_][a-z0-9_-]{0,31}$' <<<"$AGENT_USER"  || { echo "bad agent user '$AGENT_USER'"   >&2; exit 2; }
grep -qE '^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$' <<<"$TARGET_NAME" || { echo "bad target name '$TARGET_NAME'" >&2; exit 2; }
case "$WORKSPACE" in /*) ;; *) echo "workspace must be an absolute path" >&2; exit 2;; esac

command -v sshpass >/dev/null 2>&1 || {
  echo "sshpass is required on the host. Install it:  sudo pacman -S sshpass   (or apt/dnf install sshpass)" >&2
  exit 1; }

# --- MCP key store on the host (same layout vsil_hil_mcp expects) ------------
HIL="$HOME/.codeanvil-config/hil/$TARGET_NAME"
mkdir -p "$HIL"; chmod 700 "$HOME/.codeanvil-config/hil" "$HIL"
KNOWN="$HIL/known_hosts"; touch "$KNOWN"; chmod 600 "$KNOWN"
[ -f "$HIL/deploy_ed25519" ] || ssh-keygen -q -t ed25519 -N "" -C "vsil-hil-deploy-$TARGET_NAME" -f "$HIL/deploy_ed25519"
[ -f "$HIL/exec_ed25519" ]   || ssh-keygen -q -t ed25519 -N "" -C "vsil-hil-exec-$TARGET_NAME"   -f "$HIL/exec_ed25519"
chmod 600 "$HIL/deploy_ed25519" "$HIL/exec_ed25519"
DEPLOY_PUB="$(cat "$HIL/deploy_ed25519.pub")"
EXEC_PUB="$(cat "$HIL/exec_ed25519.pub")"

# --- SSH options that ignore YOUR personal credentials entirely --------------
SSH_OPTS=(
  -F /dev/null                       # ignore ~/.ssh/config
  -o IdentitiesOnly=yes
  -o IdentityAgent=none              # ignore your ssh-agent
  -o PubkeyAuthentication=no         # never offer your keys
  -o PreferredAuthentications=password
  -o GlobalKnownHostsFile=/dev/null
  -o UserKnownHostsFile="$KNOWN"     # TOFU into the MCP store, not your ~/.ssh/known_hosts
  -o StrictHostKeyChecking=accept-new
  -o ConnectTimeout=15
  -p "$PORT"
)

# --- remote setup, assembled on the host with values safely quoted -----------
REMOTE="$(cat <<REMOTE_EOF
set -euo pipefail
AGENT_USER=$(printf %q "$AGENT_USER")
WORKSPACE=$(printf %q "$WORKSPACE")
DEPLOY_PUB=$(printf %q "$DEPLOY_PUB")
EXEC_PUB=$(printf %q "$EXEC_PUB")

[ "\$(id -u)" -eq 0 ] || { echo "remote step must run as root" >&2; exit 1; }

# 1. agent user, SSH-key login only
id "\$AGENT_USER" >/dev/null 2>&1 || useradd -m -s /bin/bash "\$AGENT_USER"
passwd -l "\$AGENT_USER" >/dev/null

# 2. NOPASSWD sudo in a dedicated drop-in (never edits the main sudoers)
SUDOERS="/etc/sudoers.d/90-\$AGENT_USER"
printf '%s ALL=(ALL:ALL) NOPASSWD: ALL\n' "\$AGENT_USER" > "\$SUDOERS.tmp"
visudo -cf "\$SUDOERS.tmp" >/dev/null
install -m 0440 "\$SUDOERS.tmp" "\$SUDOERS"; rm -f "\$SUDOERS.tmp"

# 3. rrsync (restricted rsync wrapper) for the write-only deploy key
RRSYNC=\$(command -v rrsync || true)
if [ -z "\$RRSYNC" ]; then
  command -v rsync >/dev/null 2>&1 || {
    command -v apt-get >/dev/null 2>&1 && apt-get install -y rsync \
    || { command -v pacman >/dev/null 2>&1 && pacman -S --noconfirm rsync; } \
    || { command -v dnf >/dev/null 2>&1 && dnf install -y rsync; } || true; }
  for c in /usr/bin/rrsync /usr/share/doc/rsync/scripts/rrsync /usr/share/doc/rsync/examples/rrsync /usr/share/rsync/scripts/rrsync; do
    if [ -f "\$c" ]; then install -m 0755 "\$c" /usr/local/bin/rrsync; RRSYNC=/usr/local/bin/rrsync; break
    elif [ -f "\$c.gz" ]; then zcat "\$c.gz" > /usr/local/bin/rrsync; chmod 0755 /usr/local/bin/rrsync; RRSYNC=/usr/local/bin/rrsync; break; fi
  done
fi
[ -n "\$RRSYNC" ] || echo "WARN: rrsync not found — install rsync's rrsync, or code_sync will fail" >&2
RRSYNC="\${RRSYNC:-rrsync}"

# 4. workspace
install -d -o "\$AGENT_USER" -g "\$AGENT_USER" -m 0750 "\$WORKSPACE"

# 5. authorized_keys with the two MCP keys (idempotent)
HOME_DIR=\$(getent passwd "\$AGENT_USER" | cut -d: -f6)
install -d -o "\$AGENT_USER" -g "\$AGENT_USER" -m 0700 "\$HOME_DIR/.ssh"
AK="\$HOME_DIR/.ssh/authorized_keys"; touch "\$AK"
DEPLOY_LINE="command=\"\$RRSYNC -wo \$WORKSPACE\",restrict \$DEPLOY_PUB"
EXEC_LINE="restrict \$EXEC_PUB"
grep -qxF -- "\$DEPLOY_LINE" "\$AK" || printf '%s\n' "\$DEPLOY_LINE" >> "\$AK"
grep -qxF -- "\$EXEC_LINE"   "\$AK" || printf '%s\n' "\$EXEC_LINE"   >> "\$AK"
chown -R "\$AGENT_USER:\$AGENT_USER" "\$HOME_DIR/.ssh"; chmod 600 "\$AK"

echo "OK: '\$AGENT_USER' ready — locked login, NOPASSWD sudo, workspace \$WORKSPACE, deploy+exec keys installed"
REMOTE_EOF
)"

# Record the target host key into the MCP store (not your ~/.ssh/known_hosts).
ssh-keyscan -p "$PORT" -H "$TARGET_IP" >> "$KNOWN" 2>/dev/null || true

echo ">> configuring $AGENT_USER@$TARGET_IP via admin '$ADMIN_USER' (password auth; your SSH creds untouched)"
# stdin carries the admin password for `sudo -S`; the script travels base64 in the
# command argument, so it never collides with the password on stdin and works
# whether the admin login is root or a sudoer.
ENC="$(base64 -w0 <<<"$REMOTE")"
printf '%s\n' "$ADMIN_PASS" \
  | SSHPASS="$ADMIN_PASS" sshpass -e ssh "${SSH_OPTS[@]}" "$ADMIN_USER@$TARGET_IP" \
      "sudo -S -p '' bash -c 'echo $ENC | base64 -d | bash'"

cat <<DONE

✓ Credentials installed on $TARGET_IP.
  Host-side keys: $HIL/deploy_ed25519, $HIL/exec_ed25519  (private keys the MCP holds)
  Known host:     $KNOWN

Add this target to your project's .codeanvil/project.yaml:

targets:
  - name: $TARGET_NAME
    host: $TARGET_IP
    user: $AGENT_USER
    workspace: $WORKSPACE
    os: linux
    hil_policy: trusted

Then the vsil_hil_mcp tools (ssh_exec_cmd, code_sync, fetch_evidence, ...) work.
Note: running the verification kit on the target also needs CodeAnvil installed
there (curl the install.sh as $AGENT_USER); this script sets up ACCESS only.
DONE
