"""User-level tool preparation after the skill's pre-hardware review checkpoint.

Access enrollment belongs to credential-setup. The calling agent selects the
published CodeAnvil ref independently of the delivered project's ref.
"""

import shlex

DEFAULT_REPO = "https://github.com/dramirezbe/codeanvil-gcpds.git"


def render_update_command(source_ref: str, source_repo: str = DEFAULT_REPO) -> str:
    """Install a published tool source and check the capabilities the kit uses.

    The agent checks publication before the checkpoint; this command renders
    an installation, not a version manager or source attestation.
    """
    if not source_ref.strip() or source_ref != source_ref.strip() or any(c.isspace() for c in source_ref):
        raise ValueError("pass the published CodeAnvil source_ref (release tag or commit), not the DUT ref")
    if not source_repo.startswith(("https://", "ssh://")):
        raise ValueError("source_repo must identify the published CodeAnvil Git repository")
    source = shlex.quote(f"git+{source_repo}@{source_ref}")
    return (
        'set -eu\nexport PATH="$HOME/.local/bin:$PATH"\n'
        'command -v uv >/dev/null 2>&1 || { curl -LsSf https://astral.sh/uv/install.sh | sh; }\n'
        f"uv tool install --force {source}\n"
        "codeanvil init\ncodeanvil runtime sync\n"
        "codeanvil telemetry --help >/dev/null\n"
        "codeanvil now --machine\ncodeanvil --version"
    )
