#!/usr/bin/env bash
# Remote root payload. credential-setup supplies shell-quoted HIL_* variables.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo 'enrollment must run as root' >&2; exit 1; }
HIL_AGENT_USER=codeanvil-agent
id "$HIL_AGENT_USER" >/dev/null 2>&1 || useradd -m -s /bin/bash "$HIL_AGENT_USER"
HIL_HOME=$(getent passwd "$HIL_AGENT_USER" | cut -d: -f6)
HIL_GROUP=$(id -gn "$HIL_AGENT_USER")
install -d -o "$HIL_AGENT_USER" -g "$HIL_GROUP" -m 0750 "$HIL_DEPLOY_ROOT" "$HIL_WORKSPACE"

RRSYNC=$(command -v rrsync || true)
if ! command -v rsync >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then apt-get install -y rsync
  elif command -v dnf >/dev/null 2>&1; then dnf install -y rsync
  elif command -v pacman >/dev/null 2>&1; then pacman -S --noconfirm rsync
  else echo 'install rsync before enrollment' >&2; exit 1; fi
  RRSYNC=$(command -v rrsync || true)
fi
if [ "$HIL_INSTALL_DEPLOY" = yes ] && [ -z "$RRSYNC" ]; then
  for candidate in /usr/share/doc/rsync/scripts/rrsync /usr/share/doc/rsync/examples/rrsync /usr/share/rsync/scripts/rrsync; do
    if [ -f "$candidate" ]; then install -m 0755 "$candidate" /usr/local/bin/rrsync; RRSYNC=/usr/local/bin/rrsync; break
    elif [ -f "$candidate.gz" ]; then zcat "$candidate.gz" > /usr/local/bin/rrsync; chmod 0755 /usr/local/bin/rrsync; RRSYNC=/usr/local/bin/rrsync; break; fi
  done
  [ -n "$RRSYNC" ] || { echo 'rrsync is required for the dedicated deploy key' >&2; exit 1; }
fi

# Preserve every other controller's keys and all legacy forced-command lines.
install -d -o "$HIL_AGENT_USER" -g "$HIL_GROUP" -m 0700 "$HIL_HOME/.ssh"
HIL_AK="$HIL_HOME/.ssh/authorized_keys"
touch "$HIL_AK"
if [ "$HIL_INSTALL_DEPLOY" = yes ]; then
  HIL_DEPLOY_BLOB=$(printf '%s\n' "$HIL_DEPLOY_PUB" | cut -d' ' -f2)
  HIL_NEW_AK=$(mktemp "$HIL_AK.XXXXXX")
  while IFS= read -r existing || [ -n "$existing" ]; do
    case " $existing " in *" $HIL_DEPLOY_BLOB "*) ;; *) printf '%s\n' "$existing" >> "$HIL_NEW_AK" ;; esac
  done < "$HIL_AK"
  printf 'command="%s -wo %s",restrict %s\n' "$RRSYNC" "$HIL_DEPLOY_ROOT" "$HIL_DEPLOY_PUB" >> "$HIL_NEW_AK"
  chown "$HIL_AGENT_USER:$HIL_GROUP" "$HIL_NEW_AK"; chmod 0600 "$HIL_NEW_AK"
  mv "$HIL_NEW_AK" "$HIL_AK"
fi
HIL_EXEC_LINE="restrict $HIL_EXEC_PUB"
grep -qxF -- "$HIL_EXEC_LINE" "$HIL_AK" || printf '%s\n' "$HIL_EXEC_LINE" >> "$HIL_AK"
chown "$HIL_AGENT_USER:$HIL_GROUP" "$HIL_AK"; chmod 0600 "$HIL_AK"

# Existing trusted lab policy; credentials from other clients are never removed.
HIL_SUDOERS=$(mktemp)
printf '%s ALL=(ALL:ALL) NOPASSWD: ALL\n' "$HIL_AGENT_USER" > "$HIL_SUDOERS"
visudo -cf "$HIL_SUDOERS" >/dev/null
install -m 0440 "$HIL_SUDOERS" /etc/sudoers.d/90-codeanvil-agent
rm -f "$HIL_SUDOERS"
