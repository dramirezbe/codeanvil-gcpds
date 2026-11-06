"""WU-M6 Level 1: a real MCP session through `codeanvil mcp run marconi`.

Opt-in (it needs the real marconi install and GNU Radio):

    CODEANVIL_MCP_E2E=1 uv run pytest tests/test_mcp_e2e.py -v

It starts the launcher from a nested folder of a project, speaks JSON-RPC over
stdio (initialize → tools/list → tools/call run_pipeline, which runs a real
GNU Radio flowgraph), and checks that every stdout line is JSON-RPC: no log
line may leak into the protocol channel.
"""

import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.skipif(
    os.environ.get("CODEANVIL_MCP_E2E") != "1",
    reason="set CODEANVIL_MCP_E2E=1 to run the real marconi session",
)

TIMEOUT = 120


class _Session:
    def __init__(self, cwd: Path):
        env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "codeanvil", "mcp", "run", "marconi"],
            cwd=cwd, env=env, text=True, bufsize=1,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.lines: "queue.Queue[str | None]" = queue.Queue()
        self.raw: list[str] = []
        threading.Thread(target=self._pump, daemon=True).start()
        self.next_id = 0

    def _pump(self):
        for line in self.proc.stdout:
            self.raw.append(line)
            self.lines.put(line)
        self.lines.put(None)

    def send(self, method: str, params: dict | None = None, notify: bool = False):
        message = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        if not notify:
            self.next_id += 1
            message["id"] = self.next_id
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()
        if notify:
            return None
        while True:
            try:
                line = self.lines.get(timeout=TIMEOUT)
            except queue.Empty:
                pytest.fail(f"no reply to {method} within {TIMEOUT}s")
            if line is None:
                pytest.fail(f"server exited during {method}: {self.proc.stderr.read()}")
            reply = json.loads(line)
            if reply.get("id") == message["id"]:
                return reply

    def close(self):
        self.proc.stdin.close()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()


@pytest.fixture
def nested_project(tmp_path):
    root = tmp_path / "probe_project"
    (root / ".codeanvil").mkdir(parents=True)
    (root / ".codeanvil" / "project.yaml").write_text(
        yaml.safe_dump({"id": "e2e", "name": "MCP E2E"}), encoding="utf-8"
    )
    nested = root / "src" / "deep"
    nested.mkdir(parents=True)
    return root, nested


def test_marconi_runs_a_gnuradio_flowgraph_through_the_launcher(nested_project):
    root, nested = nested_project
    session = _Session(nested)
    try:
        init = session.send("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "codeanvil-e2e", "version": "1"},
        })
        assert init["result"]["serverInfo"]["name"] == "marconi"
        session.send("notifications/initialized", notify=True)

        tools = session.send("tools/list")
        names = {tool["name"] for tool in tools["result"]["tools"]}
        assert {"run_pipeline", "list_blocks"} <= names

        out = root / "tone.bin"
        call = session.send("tools/call", {"name": "run_pipeline", "arguments": {"pipeline": {
            "name": "tone_dump",
            "sample_rate": 1e6,
            "blocks": [
                {"id": "src", "type": "tone_source", "params": {"freq": 1e5, "amplitude": 0.5}},
                {"id": "head", "type": "head", "params": {"num_samples": 4096}},
                {"id": "sink", "type": "file_sink", "params": {"path": str(out)}},
            ],
            "connections": [
                {"src_block": "src", "dst_block": "head"},
                {"src_block": "head", "dst_block": "sink"},
            ],
        }}})
        result = call["result"]
        assert not result.get("isError"), result
        payload = result.get("structuredContent") or json.loads(result["content"][0]["text"])
        assert payload["status"] == "ok", payload
        # 4096 complex64 samples written by the GNU Radio flowgraph.
        assert out.stat().st_size == 4096 * 8
    finally:
        session.close()

    for line in session.raw:  # the protocol channel carries JSON-RPC only
        assert json.loads(line)["jsonrpc"] == "2.0"
