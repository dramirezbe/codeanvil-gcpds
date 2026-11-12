"""Exercise the real stdio server with local SSH/rsync stand-ins, never hardware.

The executables are on an isolated PATH, keys and project metadata live under
tmp_path, and the client uses the server's advertised MCP schemas. This tests
serialization, dispatch, policy refusal, audit and evidence return together.
"""

import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import pytest
import yaml


pytestmark = pytest.mark.skipif(os.name == "nt", reason="POSIX executable fixture; CI runs on Linux")


@pytest.fixture
def protocol_target(tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    (project / ".codeanvil").mkdir(parents=True)
    (project / ".codeanvil/project.yaml").write_text(yaml.safe_dump({
        "name": "protocol-test",
        "targets": [{"name": "pi", "host": "fixture.invalid", "user": "codeanvil-agent",
                     "workspace": "/home/codeanvil-agent/workspace", "port": 2202}],
    }), encoding="utf-8")
    key_dir = home / ".codeanvil-config/hil/pi"
    key_dir.mkdir(parents=True)
    for name in ("exec_ed25519", "deploy_ed25519", "known_hosts"):
        (key_dir / name).write_text("test-only\n", encoding="utf-8")
    executables = tmp_path / "bin"
    executables.mkdir()
    calls = tmp_path / "calls.jsonl"
    # PATH contains these stand-ins alone. An accidental real SSH connection is
    # impossible, even if a future test starts executing rsync's SSH argument.
    fake = f"""#!{sys.executable}
import json
from pathlib import Path
import sys
with open({str(calls)!r}, 'a', encoding='utf-8') as stream:
    stream.write(json.dumps(sys.argv) + '\\n')
if Path(sys.argv[0]).name == 'ssh':
    if 'VSIL_CODEANVIL' in sys.argv[-1]:
        mode_file = Path({str(calls.with_name('probe-mode'))!r})
        mode = mode_file.read_text() if mode_file.exists() else 'match'
        if mode == 'missing':
            sys.stdout.write('VSIL_OS=\\nVSIL_ARCH=\\nVSIL_CODEANVIL=\\nVSIL_USB_AVAILABLE=no\\nVSIL_USB_BEGIN\\n')
        else:
            version = '0.7.4' if mode == 'mismatch' else '0.7.5'
            sys.stdout.write('VSIL_OS=Linux\\nVSIL_ARCH=aarch64\\nVSIL_CODEANVIL=codeanvil ' + version +
                             '\\nVSIL_USB_AVAILABLE=yes\\nVSIL_USB_BEGIN\\nBus 001 Device 002: fixture SDR\\n')
        sys.exit(0)
    if sys.argv[-1] == 'fixture-timeout':
        import time
        time.sleep(5)
    if sys.argv[-1] == 'fixture-failure':
        sys.stdout.write('partial\\n')
        sys.stderr.write('failed π\\n')
        sys.exit(23)
    sys.stdout.write('line one\\nline two: á\\n')
else:
    if 'verification/telemetry/' in sys.argv[-2]:
        (Path(sys.argv[-1]) / 'telemetry-remote.jsonl').write_text('{{"sample":1}}\\n', encoding='utf-8')
    sys.stdout.write('transfer complete\\n')
"""
    for name in ("ssh", "rsync"):
        executable = executables / name
        executable.write_text(fake, encoding="utf-8")
        executable.chmod(0o755)
    # Deployment now exports a committed, published candidate. This origin is a
    # local bare repository: fetching it cannot connect to any hardware.
    git = shutil.which("git")
    if git is None:
        pytest.skip("deployment protocol fixture requires Git")
    (executables / "git").symlink_to(git)
    (project / ".gitignore").write_text("verification/telemetry/\n.codeanvil/hil/\n", encoding="utf-8")
    origin = tmp_path / "origin.git"
    for args in (["init", "-q", "-b", "main"], ["add", "."],
                 ["-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "candidate"],
                 ["init", "--bare", "-q", str(origin)], ["remote", "add", "origin", str(origin)],
                 ["push", "-qu", "origin", "main"]):
        subprocess.run([git, "-C", str(project), *args], check=True, capture_output=True, timeout=10)
    env = {
        "HOME": str(home), "PATH": str(executables),
        "VSIL_HIL_WORKSPACE": str(project), "VSIL_HIL_CODEANVIL_VERSION": "0.7.5",
        "PYTHONIOENCODING": "utf-8",
    }
    return project, calls, env


def _payload(result):
    assert not result.isError, result.content
    return json.loads(result.content[0].text)


def test_stdio_deploy_run_fetch_and_policy(protocol_target):
    project, calls, env = protocol_target
    fetched_paths = []

    async def scenario():
        params = StdioServerParameters(command=sys.executable,
                                       args=["-m", "vsil_hil_mcp.server"], env=env)
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=5)) as session:
                initialized = await session.initialize()
                assert initialized.serverInfo.name == "vsil_hil_mcp"
                tools = await session.list_tools()
                assert {"init_codeanvil", "ssh_exec_cmd", "ssh_exec_cmd_trusted",
                        "code_sync", "fetch_evidence", "probe_target"} <= {tool.name for tool in tools.tools}

                refused = _payload(await session.call_tool("ssh_exec_cmd", {"cmd": "sudo reboot"}))
                assert refused["status"] == "use_trusted"
                assert refused["command"] == "sudo reboot"
                assert not calls.exists()  # policy denial never reaches a subprocess

                deployed = _payload(await session.call_tool("code_sync", {}))
                assert deployed["exit_code"] == 0
                assert deployed["stdout"] == "transfer complete\n"
                assert len(deployed["revision"]) == 40
                observed = _payload(await session.call_tool("ssh_exec_cmd", {"cmd": "uname -a"}))
                assert observed == {"stdout": "line one\nline two: á\n", "stderr": "", "exit_code": 0}
                failure = _payload(await session.call_tool("ssh_exec_cmd_trusted", {"cmd": "fixture-failure"}))
                assert failure == {"stdout": "partial\n", "stderr": "failed π\n", "exit_code": 23}
                fetched = _payload(await session.call_tool("fetch_evidence", {}))
                assert fetched["exit_code"] == 0
                snapshot = Path(fetched["local_path"])
                assert snapshot.parent == project / "verification/telemetry/pi"
                assert snapshot.name.startswith("fetch-")
                fetched_paths.append(snapshot)
                assert json.loads((snapshot / "telemetry-remote.jsonl").read_text()) == {"sample": 1}

                missing = await session.call_tool("ssh_exec_cmd", {"cmd": "uname -a", "target": "missing"})
                assert missing.isError
                assert "unknown target" in missing.content[0].text

    asyncio.run(asyncio.wait_for(scenario(), timeout=20))
    executed = [json.loads(line) for line in calls.read_text(encoding="utf-8").splitlines()]
    assert len(executed) == 4  # deploy, normal execution, trusted failure, fetch
    push, ordinary, trusted, pull = executed
    assert Path(push[0]).name == "rsync" and "--delete" in push
    assert "deploy_ed25519" in push[push.index("-e") + 1]
    assert Path(ordinary[ordinary.index("-i") + 1]).name == "exec_ed25519"
    assert ordinary[ordinary.index("-p") + 1] == "2202"
    assert ordinary[ordinary.index("-F") + 1] == os.devnull
    assert "IdentityAgent=none" in ordinary
    assert trusted[-1] == "fixture-failure"
    assert pull[-2] == "codeanvil-agent@fixture.invalid:/home/codeanvil-agent/workspace/verification/telemetry/"
    assert pull[-1] == f"{fetched_paths[0]}/"
    audit = [json.loads(line) for line in (project / ".codeanvil/hil/audit.log").read_text().splitlines()]
    assert [(entry["tool"], entry["exit"]) for entry in audit] == [
        ("ssh_exec_cmd", None), ("code_sync", 0), ("ssh_exec_cmd", 0),
        ("ssh_exec_cmd_trusted", 23), ("fetch_evidence", 0),
    ]


def test_stdio_reports_timeout_and_missing_transport(protocol_target):
    project, calls, env = protocol_target

    async def scenario():
        # Shorten only the server's transport timeout; the real protocol and
        # subprocess code remain in use. Production commands retain 600 s.
        params = StdioServerParameters(
            command=sys.executable,
            args=["-c", "from vsil_hil_mcp import server, transport; "
                  "transport.TIMEOUT_S = 0.3; server.main()"], env=env,
        )
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=5)) as session:
                await session.initialize()
                timed_out = _payload(await session.call_tool("ssh_exec_cmd_trusted", {"cmd": "fixture-timeout"}))
                assert timed_out["exit_code"] == 124
                assert "timeout after" in timed_out["stderr"]
                (Path(env["PATH"]) / "ssh").unlink()
                missing = _payload(await session.call_tool("ssh_exec_cmd", {"cmd": "uname -a"}))
                assert missing["exit_code"] == 127
                assert missing["stderr"] == "binary not found: ssh"

    asyncio.run(asyncio.wait_for(scenario(), timeout=20))
    assert len(calls.read_text().splitlines()) == 1
    audit = [json.loads(line) for line in (project / ".codeanvil/hil/audit.log").read_text().splitlines()]
    assert [entry["exit"] for entry in audit] == [124, 127]


def test_stdio_probe_observes_parity_and_missing_data(protocol_target):
    project, calls, env = protocol_target

    async def scenario():
        params = StdioServerParameters(command=sys.executable,
                                       args=["-m", "vsil_hil_mcp.server"], env=env)
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=5)) as session:
                await session.initialize()
                tools = await session.list_tools()
                probe = next(tool for tool in tools.tools if tool.name == "probe_target")
                assert probe.annotations.readOnlyHint is True
                assert probe.annotations.destructiveHint is False
                for mode, expected_version in (("match", "0.7.5"), ("mismatch", "0.7.4"), ("missing", None)):
                    calls.with_name("probe-mode").write_text(mode, encoding="utf-8")
                    observed = _payload(await session.call_tool("probe_target", {"target": "pi"}))
                    metadata = observed["metadata"]
                    assert observed["exit_code"] == 0 and observed["stderr"] == ""
                    assert observed["target"] == "pi"
                    assert metadata["expected_version"] == "0.7.5"
                    assert metadata["codeanvil_version"] == expected_version
                    assert metadata["version_match"] is (mode == "match")
                    assert metadata["os"] == (None if mode == "missing" else "Linux")
                    assert metadata["arch"] == (None if mode == "missing" else "aarch64")
                    assert metadata["usb_probe_available"] is (mode != "missing")
                    assert metadata["usb_devices"] == ("" if mode == "missing" else "Bus 001 Device 002: fixture SDR")
                    assert f"VSIL_CODEANVIL={'codeanvil ' + expected_version if expected_version else ''}\n" in observed["stdout"]

    asyncio.run(asyncio.wait_for(scenario(), timeout=20))
    audit = [json.loads(line) for line in (project / ".codeanvil/hil/audit.log").read_text().splitlines()]
    assert [(entry["tool"], entry["exit"]) for entry in audit] == [("probe_target", 0)] * 3
