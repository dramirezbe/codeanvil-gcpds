#!/usr/bin/env bash
# codeanvil — one-line installer
# Usage: curl -fsSL https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.sh | bash
set -euo pipefail

REPO="https://github.com/dramirezbe/codeanvil-gcpds.git"
TOOL_NAME="codeanvil"
TOOL_BIN="codeanvil"
MIN_PYTHON="3.10"
SENTINEL_BEGIN="# >>> codeanvil >>>"
SENTINEL_END="# <<< codeanvil <<<"

info()  { echo "[$TOOL_NAME] $*"; }
warn()  { echo "[$TOOL_NAME] WARNING: $*" >&2; }
error() { echo "[$TOOL_NAME] ERROR: $*" >&2; exit 1; }

# ── 1. Check Python ────────────────────────────────────────────────────
check_python() {
    if ! command -v python3 &>/dev/null; then
        error "python3 not found. Install Python ${MIN_PYTHON}+ first."
    fi
    local ver
    ver="$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")"
    if python3 -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)"; then
        info "Python ${ver} found."
    else
        error "Python ${MIN_PYTHON}+ required (found ${ver})."
    fi
}

# ── 2. Ensure uv ───────────────────────────────────────────────────────
ensure_uv() {
    if command -v uv &>/dev/null; then
        return
    fi
    info "uv not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv &>/dev/null; then
        error "Failed to install uv. Install manually: https://docs.astral.sh/uv/"
    fi
    info "uv installed."
}

# ── 3. Detect shell rc file ────────────────────────────────────────────
detect_shell_rc() {
    local shell_name
    shell_name="$(basename "${SHELL:-}")"
    case "$shell_name" in
        zsh)  echo "$HOME/.zshrc" ;;
        bash)
            if [[ "$(uname -s)" == "Darwin" ]] && [[ -f "$HOME/.bash_profile" ]]; then
                echo "$HOME/.bash_profile"
            else
                echo "$HOME/.bashrc"
            fi ;;
        fish) echo "$HOME/.config/fish/config.fish" ;;
        *)    echo "" ;;
    esac
}

# ── 4. Inject PATH into shell rc (idempotent) ──────────────────────────
inject_path() {
    local rc_file="$1"
    local bin_dir="$HOME/.local/bin"

    if [[ -z "$rc_file" ]]; then
        warn "Unknown shell — add this to your shell config manually:"
        warn "  export PATH=\"$bin_dir:\$PATH\""
        return
    fi

    # Already injected
    if [[ -f "$rc_file" ]] && grep -qF "$SENTINEL_BEGIN" "$rc_file"; then
        info "PATH already configured in $(basename "$rc_file")."
        return
    fi

    local shell_name
    shell_name="$(basename "${SHELL:-}")"

    info "Adding PATH to $(basename "$rc_file")..."
    {
        echo ""
        echo "$SENTINEL_BEGIN"
        if [[ "$shell_name" == "fish" ]]; then
            echo "set -gx PATH \"$bin_dir\" \$PATH"
        else
            echo "export PATH=\"$bin_dir:\$PATH\""
        fi
        echo "$SENTINEL_END"
    } >> "$rc_file"
    info "Done. Run 'source $(basename "$rc_file")' or open a new terminal."
}

# ── 5. Install ─────────────────────────────────────────────────────────
install() {
    if uv tool list 2>/dev/null | grep -q "^${TOOL_NAME} "; then
        info "Upgrading ${TOOL_NAME}..."
        uv tool install --force-reinstall --python 3.12 "git+${REPO}"
        info "Upgraded."
        codeanvil --version 2>/dev/null || true
    else
        info "Installing ${TOOL_NAME}..."
        uv tool install --python 3.12 "git+${REPO}"
        info "Installed."
        codeanvil --version 2>/dev/null || true
    fi
}

# ── 6. Verify ──────────────────────────────────────────────────────────
verify() {
    export PATH="$HOME/.local/bin:$PATH"
    if command -v "$TOOL_BIN" &>/dev/null; then
        info "Verified: $(command -v "$TOOL_BIN")"
    else
        warn "${TOOL_BIN} not found on PATH after install."
    fi
}

# ── 7. Uninstall (called with: bash install.sh uninstall) ──────────────
uninstall() {
    info "Uninstalling ${TOOL_NAME}..."
    uv tool uninstall "$TOOL_NAME" 2>/dev/null || true

    local rc_file
    rc_file="$(detect_shell_rc)"
    if [[ -n "$rc_file" ]] && [[ -f "$rc_file" ]] && grep -qF "$SENTINEL_BEGIN" "$rc_file"; then
        sed -i.bak "/$SENTINEL_BEGIN/,/$SENTINEL_END/d" "$rc_file"
        rm -f "${rc_file}.bak"
        info "Removed PATH entry from $(basename "$rc_file")."
    fi
    info "Done."
}

# ── Main ───────────────────────────────────────────────────────────────
main() {
    if [[ "${1:-}" == "uninstall" ]]; then
        uninstall
        return
    fi

    check_python
    ensure_uv
    install
    verify

    # Inject PATH only if codeanvil isn't already reachable without it
    if ! command -v "$TOOL_BIN" &>/dev/null; then
        inject_path "$(detect_shell_rc)"
    else
        info "Ready! Run: codeanvil init && codeanvil create myproject"
    fi
}

main "$@"
