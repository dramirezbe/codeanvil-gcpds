"""FastMCP server exposing HIL tools (remote targets only, `trusted` policy MVP).

Self-contained: `mcp`, `pyyaml` and the stdlib only; never imports `codeanvil`.
"""

import json
import os
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import config, transport
from .audit import audit
from .classifier import PRIVILEGED, classify
from .provision import DEFAULT_REPO, render_update_command

mcp = FastMCP("vsil_hil_mcp")

_POLICY_MSG = "hil_policy guarded/locked: not implemented yet"


def _require_trusted(target: config.Target) -> None:
    if target.hil_policy != "trusted":
        raise NotImplementedError(_POLICY_MSG)


def _context(target: str) -> tuple[Path, config.Target, dict[str, Path]]:
    root = config.project_root()
    tgt = config.resolve_target(target, root)
    _require_trusted(tgt)
    if tgt.os != "linux":
        raise config.ConfigError("remote execution is implemented for Linux targets only")
    return root, tgt, config.key_paths(tgt.key_identity)


def _need_key(path: Path) -> Path:
    if not path.is_file():
        raise config.ConfigError(f"missing key {path}: run codeanvil credential-setup first")
    return path


def _exec(tool: str, cmd: str, target: str) -> dict:
    root, tgt, keys = _context(target)
    key = _need_key(keys["exec"])
    res = transport.ssh_run(tgt, key, cmd)
    audit(root, tgt.name, tool, cmd, res["exit_code"])
    return res


@mcp.tool()
def init_codeanvil(target: str = "", source_ref: str = "", source_repo: str = DEFAULT_REPO) -> str:
    """Install/update CodeAnvil as the enrolled agent user, then check its commands.

    The calling stage must complete its pre-hardware review checkpoint first.
    Enroll access once with codeanvil credential-setup; no keys are generated here.
    The agent supplies an actually published CodeAnvil release/commit, independently
    of the delivered project's Git ref. No exact host/target version equality gate.

    Args:
        target: declared device ID (empty if exactly one device is declared).
        source_ref: published CodeAnvil release tag or commit to install.
        source_repo: Git repository of the tool, not the DUT repository.
    """
    cmd = render_update_command(source_ref, source_repo)
    return json.dumps(_exec("init_codeanvil", cmd, target))


@mcp.tool()
def ssh_exec_cmd(cmd: str, target: str = "") -> str:
    """Run a normal lab command on the remote target; returns raw {stdout, stderr, exit_code}.

    Ordinary commands, sudo and test scripts are allowed. Explicit destructive
    operations redirect to ssh_exec_cmd_trusted before anything executes.

    Args:
        cmd: the shell command line to run on the target.
        target: target name (empty if exactly one is declared).
    """
    root, tgt, _ = _context(target)
    if classify(cmd, tgt.workspace) == PRIVILEGED:
        audit(root, tgt.name, "ssh_exec_cmd", cmd, None)
        return json.dumps({
            "status": "use_trusted",
            "command": cmd,
            "reason": "command contains an explicitly destructive operation; nothing was run. "
                      "Use ssh_exec_cmd_trusted under the host runtime's permission policy.",
        })
    return json.dumps(_exec("ssh_exec_cmd", cmd, target))


@mcp.tool()
def ssh_exec_cmd_trusted(cmd: str, target: str = "") -> str:
    """Run any command (including sudo) on the remote target, verbatim, once.

    The host runtime must configure permissions for this distinct tool. The server
    cannot verify human approval; a full-access runtime may execute it without a prompt.

    Args:
        cmd: the shell command line to run on the target.
        target: target name (empty if exactly one is declared).
    """
    return json.dumps(_exec("ssh_exec_cmd_trusted", cmd, target))


@mcp.tool()
def code_sync(target: str = "") -> str:
    """Deploy the clean, published Git candidate after the stage's pre-hardware checkpoint."""
    root, tgt, keys = _context(target)
    role = "exec" if getattr(tgt, "sync_via_exec", False) else "deploy"
    try:
        res = transport.rsync_push(tgt, _need_key(keys[role]), root)
    except config.ConfigError:
        audit(root, tgt.name, "code_sync", "unpublished or uncommitted deployment refused", None)
        raise
    audit(root, tgt.name, "code_sync", f"deploy published Git candidate {res.get('revision', '')}", res["exit_code"])
    return json.dumps({"summary": f"code_sync -> {tgt.name}:{tgt.workspace}", **res})


@mcp.tool()
def fetch_evidence(target: str = "") -> str:
    """Pull ONLY remote telemetry into a fresh host snapshot; return its local_path.

    The host destination is verification/telemetry/<target>/fetch-<unique>/.
    A nonzero exit marks a partial transfer; it cannot support an evidence claim.
    """
    root, tgt, keys = _context(target)
    res = transport.rsync_pull(tgt, _need_key(keys["exec"]), root)
    argv = transport.rsync_pull_argv(tgt, keys["exec"], root, Path(res["local_path"]))
    audit(root, tgt.name, "fetch_evidence", " ".join(argv), res["exit_code"])
    return json.dumps({"summary": f"fetch_evidence <- {tgt.name}:{tgt.workspace}/verification/telemetry/ "
                                 f"into {res['local_path']}", **res})


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False))
def probe_target(target: str = "") -> str:
    """Read OS, architecture, installed CodeAnvil version and USB visibility.

    The device declaration is reported separately from observed lsusb output.
    Versions are diagnostic; the agent prepares missing capabilities after review.
    This probe does not transmit RF, install packages or edit target configuration.
    """
    root, tgt, keys = _context(target)
    expected = os.environ.get("VSIL_HIL_CODEANVIL_VERSION") or None
    res = transport.ssh_run(tgt, _need_key(keys["exec"]), transport.PROBE_CMD)
    audit(root, tgt.name, "probe_target", transport.PROBE_CMD, res["exit_code"])
    fields, usb_lines = {}, []
    in_usb = False
    for line in res["stdout"].splitlines():
        if line == "VSIL_USB_BEGIN":
            in_usb = True
        elif in_usb:
            usb_lines.append(line)
        elif line.startswith("VSIL_") and "=" in line:
            key, value = line.split("=", 1)
            fields[key] = value
    version_text = fields.get("VSIL_CODEANVIL", "")
    match = re.fullmatch(r"codeanvil (\S+)", version_text)
    observed_version = match.group(1) if match else None
    metadata = {
        "os": fields.get("VSIL_OS") or None,
        "arch": fields.get("VSIL_ARCH") or None,
        "codeanvil_version": observed_version,
        "expected_version": expected,
        "version_match": res["exit_code"] == 0 and observed_version == expected,
        "declared_device": tgt.device,
        "usb_probe_available": fields.get("VSIL_USB_AVAILABLE") == "yes",
        "usb_devices": "\n".join(usb_lines),
    }
    return json.dumps({"target": tgt.name, "metadata": metadata, **res})


def main() -> None:
    """Console entry point: serve over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
