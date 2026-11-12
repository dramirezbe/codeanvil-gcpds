"""FastMCP server exposing HIL tools (remote targets only, `trusted` policy MVP).

Self-contained: `mcp`, `pyyaml` and the stdlib only; never imports `codeanvil`.
"""

import json
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import config, transport
from .audit import audit
from .classifier import PRIVILEGED, classify
from .provision import render_script

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
    return root, tgt, config.key_paths(tgt.name)


def _need_key(path: Path) -> Path:
    if not path.is_file():
        raise config.ConfigError(f"missing key {path}: run init_codeanvil first")
    return path


def _exec(tool: str, cmd: str, target: str) -> dict:
    root, tgt, keys = _context(target)
    key = _need_key(keys["exec"])
    res = transport.ssh_run(tgt, key, cmd)
    audit(root, tgt.name, tool, cmd, res["exit_code"])
    return res


@mcp.tool()
def init_codeanvil(
    target: str = "", host: str = "", user: str = "codeanvil-agent", workspace: str = "",
    os: str = "linux", arch: str = "", device: str = "", hil_policy: str = "trusted", port: int = 22,
) -> str:
    """Prepare a remote target: create its keys and return the provisioning script.

    No SSH happens here. The returned script must be read and run ONCE, as root,
    by the human on the target. If `target` is not yet declared in
    `.codeanvil/project.yaml` `targets:`, pass host/user (and optionally
    workspace/os/arch/device/hil_policy) to register it.

    Args:
        target: target name; may be empty when exactly one target is declared.
        host: target address (only to register a new target).
        user: fixed codeanvil-agent user for new targets; existing declarations retain their user.
        workspace: absolute workspace path on the target (default /home/<user>/workspace).
        os: target OS, "linux" or "windows" (windows provisioning is not implemented).
        arch: target architecture, e.g. aarch64.
        device: declared SDR device.
        hil_policy: trusted (only mode implemented).
        port: SSH port, from 1 to 65535 (new target).
    """
    root = config.project_root()
    declared = config.load_targets(root)
    if target in declared or (not target and len(declared) == 1):
        tgt = declared[target] if target else next(iter(declared.values()))
    else:
        if not target or not host or not user:
            raise config.ConfigError("undeclared target: pass target, host and user to register it")
        ws = workspace or f"/home/{user}/workspace"
        config.validate_target_fields(target, host, user, ws, hil_policy, port, os)
        if user != config.AGENT_USER:
            raise config.ConfigError("new targets must use the fixed codeanvil-agent user")
        tgt = config.Target(target, host, user, ws, os, arch, device, hil_policy, port)
    _require_trusted(tgt)
    if tgt.os.lower() != "linux":
        raise config.ConfigError("provisioning is implemented for Linux targets only")
    version = config.host_version()

    keys = config.ensure_key_dir(tgt.name)
    for kind in ("deploy", "exec"):
        if not keys[kind].exists():
            res = transport.keygen(keys[kind], f"vsil-hil-{kind}-{tgt.name}")
            if res["exit_code"] != 0:
                raise RuntimeError(f"ssh-keygen failed: {res['stderr'].strip()}")
    config.lock_key_perms(keys)

    deploy_pub = keys["deploy"].with_name("deploy_ed25519.pub").read_text(encoding="utf-8")
    exec_pub = keys["exec"].with_name("exec_ed25519.pub").read_text(encoding="utf-8")
    script = render_script(tgt, deploy_pub, exec_pub, version)
    registered = config.register_target(root, tgt)
    audit(root, tgt.name, "init_codeanvil", "ssh-keygen + provisioning script emitted", 0)
    return (
        f"INSTRUCTIONS FOR THE HUMAN (target {tgt.name!r}, registered={registered}).\n"
        f"1. Copy the script below to {tgt.user}@{tgt.host} (or any admin account there) and read it.\n"
        "2. Run it once as root on the target: sudo bash provision.sh\n"
        "3. Compare the printed host key fingerprints with what ssh records on first contact\n"
        f"   (stored in {keys['known_hosts']}).\n"
        "4. Then use code_sync / ssh_exec_cmd. The agent holds no credentials.\n"
        "----- provision.sh -----\n" + script
    )


@mcp.tool()
def ssh_exec_cmd(cmd: str, target: str = "") -> str:
    """Run a non-privileged command on the remote target; returns raw {stdout, stderr, exit_code}.

    Unknown commands, mutations and shell expansions are refused. Python/uv/pytest
    and verification/run.sh vl0|vl1 require `cd <declared workspace> &&`.

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
            "reason": "command is outside the automatic command policy; nothing was run. "
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
    """Deploy the project's code to the target workspace (rsync, deploy key, write-only)."""
    root, tgt, keys = _context(target)
    argv = transport.rsync_push_argv(tgt, _need_key(keys["deploy"]), root)
    res = transport.rsync_push(tgt, keys["deploy"], root)
    audit(root, tgt.name, "code_sync", " ".join(argv), res["exit_code"])
    return json.dumps({"summary": f"code_sync -> {tgt.name}:{tgt.workspace}", **res})


@mcp.tool()
def fetch_evidence(target: str = "") -> str:
    """Pull ONLY verification/telemetry/ from the target into the project."""
    root, tgt, keys = _context(target)
    argv = transport.rsync_pull_argv(tgt, _need_key(keys["exec"]), root)
    res = transport.rsync_pull(tgt, keys["exec"], root)
    audit(root, tgt.name, "fetch_evidence", " ".join(argv), res["exit_code"])
    return json.dumps({"summary": f"fetch_evidence <- {tgt.name}:{tgt.workspace}/verification/telemetry/", **res})


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False))
def probe_target(target: str = "") -> str:
    """Read OS, architecture, installed CodeAnvil version and USB visibility.

    The device declaration is reported separately from observed lsusb output.
    Version mismatch or an unavailable observation is never reported as parity.
    This probe does not transmit RF, install packages or edit target configuration.
    """
    root, tgt, keys = _context(target)
    expected = config.host_version()
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
    match = re.fullmatch(r"codeanvil ([0-9]+\.[0-9]+\.[0-9]+)", version_text)
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
