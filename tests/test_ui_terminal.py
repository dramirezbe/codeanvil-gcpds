"""The local terminal API uses real PTYs and fixture programs, never an LLM."""

import os
import sys
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from codeanvil.UI import terminal
from codeanvil.UI.ui import create_app


pytestmark = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux/WSL PTYs")
ORIGIN = {"origin": "http://localhost"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / ".codeanvil").mkdir(parents=True)
    (project / ".codeanvil/project.yaml").write_text("id: test-id\nname: Terminal test\n")
    monkeypatch.setattr(terminal.launchers, "scan", lambda: [
        {"id": "fixture", "label": "Fixture", "kind": "terminal", "installed": True, "available": True},
        {"id": "gui", "label": "Editor", "kind": "gui", "installed": True, "available": True},
        {"id": "absent", "label": "Absent", "kind": "terminal", "installed": False, "available": True},
    ])
    script = (
        "import os,sys; print('READY '+os.getcwd(),flush=True); "
        "print('ANSWER '+input(),flush=True)"
    )
    monkeypatch.setattr(terminal.launchers, "launch", lambda identifier, root: {
        "kind": "terminal", "cwd": str(root), "argv": [sys.executable, "-u", "-c", script],
    })
    with TestClient(create_app(project), base_url="http://localhost") as test_client:
        yield test_client, project


def start(client, project, **changes):
    return client.post("/api/terminal/sessions", json={
        "project_path": str(project), "launcher_id": "fixture", **changes,
    }, headers=ORIGIN)


def test_launchers_exclude_gui_and_expose_sandbox_support(client):
    http, _ = client
    data = http.get("/api/terminal/launchers").json()
    assert data["supported"] is True
    assert [item["id"] for item in data["launchers"]] == ["fixture", "absent"]
    assert data["launchers"][0]["sandbox_supported"] is False


def test_real_terminal_input_replay_exit_and_reconnect(client):
    http, project = client
    response = start(http, project)
    assert response.status_code == 200, response.text
    session = response.json()
    assert session["sandbox"] is False and session["pid"] > 0
    assert start(http, project).status_code == 409
    url = f"ws://localhost/api/terminal/sessions/{session['id']}/stream"
    with http.websocket_connect(url, headers=ORIGIN) as ws:
        assert ws.receive_json()["type"] == "ready"
        data = b""
        while b"READY " not in data:
            data += ws.receive_bytes()
        assert str(project).encode() in data
        ws.send_json({"type": "resize", "cols": 120, "rows": 35})
        ws.send_json({"type": "input", "data": "hola terminal\r"})
        messages = []
        while True:
            message = ws.receive()
            if "bytes" in message:
                data += message["bytes"]
            else:
                import json
                messages.append(json.loads(message["text"]))
                if messages[-1]["type"] == "exit":
                    break
        assert b"ANSWER hola terminal" in data
        assert messages[-1] == {"type": "exit", "code": 0}
    with http.websocket_connect(url, headers=ORIGIN) as ws:
        assert ws.receive_json()["session"]["state"] == "exited"
        assert b"ANSWER hola terminal" in ws.receive_bytes()
        assert ws.receive_json() == {"type": "exit", "code": 0}


def test_disconnect_does_not_stop_process_and_stop_is_idempotent(client):
    http, project = client
    session = start(http, project).json()
    with http.websocket_connect(f"ws://localhost/api/terminal/sessions/{session['id']}/stream", headers=ORIGIN) as ws:
        assert ws.receive_json()["type"] == "ready"
    assert http.get("/api/terminal/sessions", params={"project_path": str(project)}).json()["sessions"][0]["state"] == "running"
    for _ in range(2):
        response = http.post(f"/api/terminal/sessions/{session['id']}/stop", json={}, headers=ORIGIN)
        assert response.status_code == 200
        assert response.json()["state"] == "exited"
    with pytest.raises(ProcessLookupError):
        os.kill(session["pid"], 0)


@pytest.mark.parametrize("changes,code", [
    ({"launcher_id": "unknown"}, 400),
    ({"launcher_id": "gui"}, 400),
    ({"launcher_id": "absent"}, 409),
    ({"sandbox": True}, 400),
    ({"cols": 0}, 422),
    ({"argv": ["sh"]}, 422),
    ({"sandbox": "false"}, 422),
])
def test_start_rejects_unknown_commands_modes_and_dimensions(client, changes, code):
    http, project = client
    assert start(http, project, **changes).status_code == code
    assert http.get("/api/terminal/sessions").json() == {"sessions": []}


def test_project_validation_and_browser_origin_are_required(client, tmp_path):
    http, project = client
    assert start(http, tmp_path).status_code == 404
    payload = {"project_path": str(project), "launcher_id": "fixture"}
    for headers in ({}, {"origin": "http://localhost:9999"}, {"origin": "https://evil.invalid"}):
        assert http.post("/api/terminal/sessions", json=payload, headers=headers).status_code == 403
    session = start(http, project).json()
    for headers in ({}, {"origin": "http://localhost:9999"}, {"origin": "https://evil.invalid"}):
        with pytest.raises(WebSocketDisconnect) as error:
            with http.websocket_connect(f"ws://localhost/api/terminal/sessions/{session['id']}/stream", headers=headers):
                pass
        assert error.value.code == 1008


def test_invalid_stream_message_closes_connection_but_keeps_process(client):
    http, project = client
    session = start(http, project).json()
    with http.websocket_connect(f"ws://localhost/api/terminal/sessions/{session['id']}/stream", headers=ORIGIN) as ws:
        ws.receive_json()
        ws.send_json({"type": "resize", "cols": -1, "rows": 30})
        while True:
            message = ws.receive()
            if message["type"] == "websocket.close":
                assert message["code"] == 1008
                break
    assert http.get("/api/terminal/sessions").json()["sessions"][0]["state"] == "running"


def test_sandbox_context_lives_until_process_exit(client, monkeypatch):
    from contextlib import contextmanager
    http, project = client
    entered = []
    @contextmanager
    def sandbox(identifier, root):
        entered.append("enter")
        try:
            yield terminal.launchers.launch(identifier, root) | {"env": dict(os.environ)}
        finally:
            entered.append("exit")
    monkeypatch.setattr(terminal, "prepare_sandbox", sandbox)
    monkeypatch.setattr(terminal, "SANDBOX_AGENTS", {"fixture": {}})
    session = start(http, project, sandbox=True).json()
    assert session["sandbox"] is True and entered == ["enter"]
    http.post(f"/api/terminal/sessions/{session['id']}/stop", json={}, headers=ORIGIN)
    assert entered == ["enter", "exit"]


def test_app_shutdown_reaps_owned_process(tmp_path, monkeypatch):
    project = tmp_path / "shutdown"
    (project / ".codeanvil").mkdir(parents=True)
    (project / ".codeanvil/project.yaml").write_text("id: shutdown\nname: Shutdown\n")
    monkeypatch.setattr(terminal.launchers, "scan", lambda: [
        {"id": "fixture", "kind": "terminal", "installed": True, "available": True},
    ])
    monkeypatch.setattr(terminal.launchers, "launch", lambda *_: {
        "kind": "terminal", "argv": [sys.executable, "-c", "import time; time.sleep(60)"],
    })
    with TestClient(create_app(project), base_url="http://localhost") as http:
        session = start(http, project).json()
    with pytest.raises(ProcessLookupError):
        os.kill(session["pid"], 0)


def test_binary_websocket_input_is_rejected_with_a_close_frame(client):
    http, project = client
    session = start(http, project).json()
    with http.websocket_connect(f"ws://localhost/api/terminal/sessions/{session['id']}/stream", headers=ORIGIN) as ws:
        ws.receive_json()
        ws.send_bytes(b"binary")
        while True:
            message = ws.receive()
            if message["type"] == "websocket.close":
                assert message["code"] == 1008
                break
    assert http.get("/api/terminal/sessions").json()["sessions"][0]["state"] == "running"


def test_failed_start_closes_prepared_sandbox_and_registers_nothing(client, monkeypatch):
    http, project = client
    lifecycle = []

    @contextmanager
    def sandbox(*args):
        lifecycle.append("enter")
        try:
            yield {"argv": ["fixture"]}
        finally:
            lifecycle.append("exit")

    def failed(*args):
        raise terminal.PtyError("fixture cannot spawn")

    monkeypatch.setattr(terminal, "prepare_sandbox", sandbox)
    monkeypatch.setattr(terminal, "SANDBOX_AGENTS", {"fixture": {}})
    monkeypatch.setattr("codeanvil.UI.terminal_sessions.PtyProcess.start", failed)
    assert start(http, project, sandbox=True).status_code == 400
    assert lifecycle == ["enter", "exit"]
    assert http.get("/api/terminal/sessions").json() == {"sessions": []}


def test_native_windows_reports_unavailable_without_spawning(client, monkeypatch):
    http, project = client
    monkeypatch.setattr(terminal.sys, "platform", "win32")
    assert http.get("/api/terminal/launchers").json()["supported"] is False
    assert start(http, project).status_code == 501
    assert http.get("/api/terminal/sessions").json() == {"sessions": []}


@pytest.mark.parametrize("raw", ["{broken", "[]", '{"type":"input","data":1}', "x" * 65537])
def test_invalid_json_or_payload_closes_without_stopping_cli(client, raw):
    http, project = client
    session = start(http, project).json()
    with http.websocket_connect(f"ws://localhost/api/terminal/sessions/{session['id']}/stream", headers=ORIGIN) as ws:
        ws.receive_json()
        ws.send_text(raw)
        while True:
            message = ws.receive()
            if message["type"] == "websocket.close":
                assert message["code"] == 1008
                break
    assert http.get("/api/terminal/sessions").json()["sessions"][0]["state"] == "running"
