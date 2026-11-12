"""Small destructive-command router, not a shell interpreter or sandbox.

Normal shell commands, sudo, package installs and scripts use the automatic door.
Only recognizable destructive operations below require the trusted tool. Scripts
can perform work invisible here: an agent that knows a script destroys data must
choose trusted itself. The host runtime governs approvals on that separate tool.
"""

import re
import shlex
from pathlib import PurePosixPath

ALLOW = "ALLOW"
PRIVILEGED = "PRIVILEGED"

_DESTRUCTIVE = {"systemctl", "reboot", "shutdown", "poweroff", "halt", "dd", "shred",
                "wipefs", "blkdiscard", "fdisk", "sfdisk", "cfdisk", "parted", "mkswap", "mke2fs"}
_DATABASE_TOOLS = {"sqlite", "sqlite3", "psql", "mysql", "mariadb", "mongo", "mongosh", "redis-cli"}
_DATABASE_WRITERS = {"rm", "mv", "cp", "truncate", "tee", "install", "touch", "sed", "rsync"}
_DATABASE_PATH = re.compile(r"\.(?:db|db3|sqlite|sqlite3|duckdb|mdb|rdb)(?:-(?:wal|shm|journal))?$", re.I)
_DATABASE_DIRS = {"database", "databases", "postgresql", "mysql", "mariadb", "mongodb", "redis"}
_WRAPPERS = {"sudo", "env", "command", "builtin", "nohup", "nice", "time"}
_WRAPPER_VALUE_OPTIONS = {"-u", "--user", "-g", "--group", "-h", "--host", "-p", "--prompt",
                          "-C", "--close-from", "-T", "--command-timeout", "-R", "--chroot",
                          "-D", "--chdir", "-n", "--adjustment"}


def _database(path: str) -> bool:
    return bool(_DATABASE_PATH.search(path)) or bool(set(PurePosixPath(path).parts) & _DATABASE_DIRS)


def _unwrap(words: list[str]) -> list[str]:
    """Skip familiar command prefixes; do not inspect interpreter/script bodies."""
    while words and ("=" in words[0] and not words[0].startswith("-")):
        words = words[1:]
    while words and PurePosixPath(words[0]).name in _WRAPPERS:
        wrapper, words = PurePosixPath(words[0]).name, words[1:]
        while words and (words[0].startswith("-") or (wrapper == "env" and "=" in words[0])):
            option, words = words[0], words[1:]
            if option in _WRAPPER_VALUE_OPTIONS and not (wrapper == "sudo" and option == "-n") and words:
                words = words[1:]
    return words


def _destructive(words: list[str]) -> bool:
    words = _unwrap(words)
    if not words:
        return False
    command, *args = words
    command = PurePosixPath(command).name
    if command in _DESTRUCTIVE or command.startswith("mkfs") or command in _DATABASE_TOOLS:
        return True
    if command == "rm":
        for arg in args:
            if arg == "--":
                break
            if arg == "--recursive" or (arg.startswith("-") and not arg.startswith("--") and any(c in arg for c in "rR")):
                return True
    return command in _DATABASE_WRITERS and any(_database(arg) for arg in args)


def classify(cmd: str, workspace: str = "") -> str:
    """Route visible destructive commands, including those in compound shell lines.

    ``workspace`` remains accepted for existing callers; normal execution no longer
    requires a special cwd prefix. Malformed or opaque script syntax is left to
    the remote shell rather than pretending this router can prove what it does.
    """
    try:
        lexer = shlex.shlex(cmd.replace("\n", ";"), posix=True, punctuation_chars="|&;()<>")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return ALLOW
    words = []
    for index, token in enumerate(tokens):
        if token and all(c in "|&;()<>" for c in token):
            if _destructive(words):
                return PRIVILEGED
            if ">" in token and index + 1 < len(tokens) and _database(tokens[index + 1]):
                return PRIVILEGED
            words = []
        else:
            words.append(token)
    return PRIVILEGED if _destructive(words) else ALLOW
