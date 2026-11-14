"""Optional offline acceptance against an installed Codex CLI (no model calls)."""

import json
import os
from queue import Queue, Empty
import shutil
import subprocess
from threading import Thread

import pytest
import tomlkit

from codeanvil.init.create import scaffold_project


@pytest.mark.skipif(shutil.which("codex") is None, reason="Codex CLI is not installed")
def test_codex_reads_scaffold_mcp_and_discovers_skills(tmp_path):
    project = scaffold_project("Codex acceptance", "project", tmp_path, mcp_servers=["vsil_hil_mcp"])
    module = project / "services" / "receiver"
    module.mkdir(parents=True)
    home = tmp_path / "codex-home"
    home.mkdir()
    # Fixture trust only: never read or modify the developer's Codex settings.
    (home / "config.toml").write_text(tomlkit.dumps({
        "projects": {str(project): {"trust_level": "trusted"}},
    }), encoding="utf-8")
    env = {**os.environ, "CODEX_HOME": str(home)}
    listed = subprocess.run(
        ["codex", "mcp", "list", "--json"], cwd=module, env=env,
        capture_output=True, text=True, timeout=30, check=True,
    )
    server = next(s for s in json.loads(listed.stdout) if s["name"] == "vsil_hil_mcp")
    assert server["transport"]["command"] == "codeanvil"
    assert server["transport"]["args"] == ["mcp", "run", "vsil_hil_mcp"]

    with subprocess.Popen(
        ["codex", "app-server", "--stdio", "--strict-config"],
        cwd=project, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True,
    ) as process:
        replies = Queue()

        def read_replies():
            for line in process.stdout:
                replies.put(json.loads(line))

        reader = Thread(target=read_replies, daemon=True)
        reader.start()
        try:
            def request(request_id, method, params):
                process.stdin.write(json.dumps({"id": request_id, "method": method, "params": params}) + "\n")
                process.stdin.flush()
                try:
                    while True:
                        reply = replies.get(timeout=15)
                        if reply.get("id") == request_id:
                            assert "error" not in reply, reply
                            return reply["result"]
                except Empty:
                    pytest.fail(f"Codex timed out during {method}")

            request(1, "initialize", {"clientInfo": {"name": "codeanvil-test", "version": "1"}})
            process.stdin.write('{"method":"initialized"}\n')
            process.stdin.flush()
            result = request(2, "skills/list", {"cwds": [str(project), str(module)], "forceReload": True})
            expected = {str(path) for path in (project / ".agents/skills").glob("*/SKILL.md")}
            assert expected
            assert len(result["data"]) == 2
            for discovered in result["data"]:
                assert not discovered["errors"], discovered["errors"]
                paths = {skill["path"] for skill in discovered["skills"]}
                assert expected <= paths
        finally:
            process.terminate()
            process.wait(timeout=10)
            reader.join(timeout=5)
