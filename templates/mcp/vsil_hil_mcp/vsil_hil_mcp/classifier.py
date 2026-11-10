"""Coarse command classifier.

NOT a security boundary. It only stops an accidental direct `sudo` on the auto
door; target OS isolation and the runtime prompt on `ssh_exec_cmd_trusted` are
the real gates. A script that calls sudo internally is invisible to it.
"""

import re

ALLOW = "ALLOW"
PRIVILEGED = "PRIVILEGED"

_SUDO = re.compile(r"\bsudo\b")


def classify(cmd: str) -> str:
    return PRIVILEGED if _SUDO.search(cmd) else ALLOW
