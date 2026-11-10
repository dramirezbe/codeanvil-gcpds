"""FastMCP server exposing the five HIL tools.

SKELETON: every tool body is a stub. The real ssh/rsync transport, credential
custody and command classifier land in tasks T4/T5 of the hil-mcp plan.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("vsil_hil_mcp")

_NOT_IMPLEMENTED = "T4/T5: not implemented"


@mcp.tool()
def init_codeanvil(target: str) -> str:
    """Install CodeAnvil on the declared target and build its methodology runtime.

    Args:
        target: target id declared in the project's `.codeanvil/project.yaml` `targets:` block.
    """
    raise NotImplementedError(_NOT_IMPLEMENTED)


@mcp.tool()
def ssh_exec_cmd(cmd: str) -> str:
    """Run a command on the target through the classifier (allow / ask / deny).

    Args:
        cmd: the shell command line to run on the target.
    """
    raise NotImplementedError(_NOT_IMPLEMENTED)


@mcp.tool()
def ssh_exec_cmd_trusted(cmd: str) -> str:
    """Run a command on the target, bypassing the classifier's ASK tier (human-trusted).

    Args:
        cmd: the shell command line to run on the target.
    """
    raise NotImplementedError(_NOT_IMPLEMENTED)


@mcp.tool()
def code_sync() -> str:
    """Deploy the project's delivered code to the target (rsync, forced-command)."""
    raise NotImplementedError(_NOT_IMPLEMENTED)


@mcp.tool()
def fetch_evidence() -> str:
    """Pull run evidence (logs, telemetry, measurement files) from the target to the host."""
    raise NotImplementedError(_NOT_IMPLEMENTED)


def main() -> None:
    """Console entry point: serve over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
