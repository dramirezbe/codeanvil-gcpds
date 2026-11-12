"""Conservative routing for the automatic SSH door, not an execution sandbox.

Unknown commands and shell syntax go to the separately permissioned trusted tool.
Allowed Python, uv and CodeAnvil can execute arbitrary user code; target isolation
and the host runtime's configured permissions remain the actual boundaries.
"""

import re
import shlex

ALLOW = "ALLOW"
PRIVILEGED = "PRIVILEGED"

_READ_ONLY = frozenset({
    "ls", "cat", "stat", "uname", "df", "free", "head", "tail", "wc", "pwd",
    "whoami", "id", "lsusb", "lscpu", "lspci", "uptime", "nproc",
    "readlink", "realpath", "grep", "sha256sum",
})
_WORKSPACE_RUNNERS = frozenset({"python", "python3", "pytest", "uv"})
# Shell expansion is intentionally refused even inside quotes. This coarse gate
# may ask for a harmless command, but must not silently evaluate substitutions.
_SHELL_EXPANSION = re.compile(r"[$`\n\r\x00]")


def _command_allowed(words: list[str], in_workspace: bool) -> bool:
    executable, *args = words
    if executable in _READ_ONLY:
        return True
    if executable == "hostname":
        return all(a in {"-s", "--short", "-f", "--fqdn", "-i", "--ip-address", "-I", "--all-ip-addresses"}
                   for a in args)
    if executable == "find":
        return not any(a in {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fls"}
                       or a.startswith(("-fprint", "-fprintf")) for a in args)
    if executable == "dmesg":
        return all(a in {"-T", "--ctime", "-H", "--human", "-k", "--kernel", "-x", "--decode"}
                   for a in args)
    if executable == "vcgencmd":
        return bool(args) and args[0] in {
            "get_throttled", "measure_temp", "measure_clock", "measure_volts", "version",
        }
    if executable == "SoapySDRUtil":
        return bool(args) and all(a in {"--info", "--find", "--probe"}
                                  or a.startswith(("--find=", "--probe=")) for a in args)
    if executable == "rtl_test":
        return not args or args == ["-t"]
    # Full CodeAnvil control is an explicitly granted capability, including its
    # Python runner. An absolute user-bin executable avoids non-login SSH PATH issues.
    if executable == "codeanvil" or re.fullmatch(r"/home/[a-z_][a-z0-9_-]*/\.local/bin/codeanvil", executable):
        return True
    if executable in _WORKSPACE_RUNNERS:
        return in_workspace
    if executable in {"verification/run.sh", "./verification/run.sh"}:
        return in_workspace and len(args) == 1 and args[0] in {"vl0", "vl1"}
    return False


def classify(cmd: str, workspace: str = "") -> str:
    """Allow known diagnostics or runners after an exact workspace ``cd``.

    Only ``&&`` and diagnostic pipes are recognized. Redirection, background
    execution, compound shell syntax and mutations require the trusted tool.
    """
    if not cmd.strip() or _SHELL_EXPANSION.search(cmd):
        return PRIVILEGED
    try:
        lexer = shlex.shlex(cmd, posix=True, punctuation_chars="|&;()<>")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return PRIVILEGED
    segments: list[tuple[list[str], str]] = []
    words: list[str] = []
    for token in tokens:
        if token and all(c in "|&;()<>" for c in token):
            if token not in {"&&", "|"} or not words:
                return PRIVILEGED
            segments.append((words, token))
            words = []
        else:
            words.append(token)
    if not words:
        return PRIVILEGED
    segments.append((words, ""))
    in_workspace = False
    for words, separator in segments:
        if words[0] == "cd":
            if words != ["cd", workspace] or not workspace or separator != "&&":
                return PRIVILEGED
            in_workspace = True
        elif not _command_allowed(words, in_workspace):
            return PRIVILEGED
        # A cd in a pipeline cannot establish cwd for the next process.
        if separator == "|":
            in_workspace = False
    return ALLOW
