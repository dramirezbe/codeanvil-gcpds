"""HTTP adapter for the existing CodeAnvil CLI logic.

The browser sends parser arguments; the backend dispatches through the same
Python command functions as the console entry point. It never shells out to
the ``codeanvil`` executable.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import logging
import os
import threading
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from codeanvil.CLI.main import choose_option
from codeanvil.CLI.parser import build_parser
from codeanvil.config.paths import find_manifest

_CWD_LOCK = threading.RLock()
_BLOCKED = {
    "python": "Running arbitrary Python scripts requires the live terminal feature.",
    "sandbox": "Launching an agent requires the live terminal feature.",
    "mcp.run": "Starting a long-running MCP server is not a one-shot UI action.",
}
_CONFIRM = {
    "init", "upgrade", "credential-setup", "mcp.add", "mcp.update",
    "mcp.remove", "mcp.enable", "mcp.disable", "runtime.sync", "runtime.add",
    "runtime.remove", "create", "sync", "backup", "telemetry",
}
_ALLOWED_TOP = {
    "init", "create", "list", "sync", "status", "backup", "runtime",
    "mcp", "now", "telemetry", "credential-setup", "upgrade", "python", "sandbox",
}


class ActionRequest(BaseModel):
    argv: list[str] = Field(min_length=1, max_length=64)
    project_path: str | None = None
    confirm: bool = False


def _subparser_action(parser: argparse.ArgumentParser) -> argparse._SubParsersAction | None:
    return next((a for a in parser._actions if isinstance(a, argparse._SubParsersAction)), None)


def _field(action: argparse.Action) -> dict[str, Any] | None:
    if isinstance(action, (argparse._HelpAction, argparse._VersionAction)):
        return None
    positional = not bool(action.option_strings)
    flag = None if positional else next(
        (s for s in action.option_strings if s.startswith("--")), action.option_strings[0]
    )
    name = action.dest
    if action.nargs == 0:
        kind = "boolean"
    elif action.choices:
        kind = "select"
    elif action.type is Path:
        kind = "path"
    elif action.type in (int, float):
        kind = "number"
    else:
        kind = "text"
    nargs = action.nargs
    multiple = isinstance(action, argparse._AppendAction) or nargs in ("+", "*")
    default = None if action.default is argparse.SUPPRESS else action.default
    return {
        "name": name,
        "label": name.replace("_", " "),
        "flag": flag,
        "positional": positional,
        "type": kind,
        "required": bool(
            getattr(action, "required", False)
            or (positional and nargs not in ("?", "*"))
        ),
        "multiple": multiple,
        "nargs": str(nargs) if nargs is not None else None,
        "choices": list(action.choices) if action.choices is not None else None,
        "default": str(default) if isinstance(default, Path) else default,
        "secret": "password" in name.lower(),
        "help": action.help or "",
    }


def _parser_fields(parser: argparse.ArgumentParser) -> list[dict[str, Any]]:
    nested = _subparser_action(parser)
    result = []
    for action in parser._actions:
        if action is nested:
            continue
        field = _field(action)
        if field is not None:
            result.append(field)
    return result


def _catalog() -> list[dict[str, Any]]:
    parser = build_parser()
    subparsers = _subparser_action(parser)
    if subparsers is None:
        return []
    actions: list[dict[str, Any]] = []
    for top, child in subparsers.choices.items():
        if top not in _ALLOWED_TOP or top == "ui":
            continue
        nested = _subparser_action(child)
        if nested is None:
            action_id = top
            blocked = _BLOCKED.get(action_id)
            actions.append({
                "id": action_id,
                "label": top.replace("-", " ").title(),
                "help": next((a.help for a in subparsers._choices_actions if a.dest == top), ""),
                "argv_prefix": [top],
                "available": blocked is None,
                "reason": blocked,
                "requires_confirmation": action_id in _CONFIRM,
                "requires_project_path": top == "sync",
                "fields": _parser_fields(child),
            })
            continue
        common = _parser_fields(child)
        for subcommand, subparser in nested.choices.items():
            action_id = f"{top}.{subcommand}"
            blocked = _BLOCKED.get(action_id)
            actions.append({
                "id": action_id,
                "label": f"{top} {subcommand}",
                "help": next((a.help for a in nested._choices_actions if a.dest == subcommand), ""),
                "argv_prefix": [top, subcommand],
                "available": blocked is None,
                "reason": blocked,
                "requires_confirmation": action_id in _CONFIRM,
                "fields": common + _parser_fields(subparser),
            })
    return actions


def _selected_cwd(root: Path, project_path: str | None) -> Path:
    if project_path is None:
        return root
    manifest = find_manifest(Path(project_path).expanduser().resolve())
    if manifest is None:
        raise HTTPException(status_code=404, detail="Selected path is not a CodeAnvil project")
    return manifest.parent.parent.resolve()


def _requires_confirmation(argv: list[str]) -> bool:
    if argv[0] in {"mcp", "runtime"} and len(argv) > 1:
        return f"{argv[0]}.{argv[1]}" in _CONFIRM
    return argv[0] in _CONFIRM


def _redact(text: str, secrets: list[str]) -> str:
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[redacted]")
    return text


@contextlib.contextmanager
def _capture_log_stream(stderr: io.StringIO):
    handlers = list(logging.getLogger().handlers)
    handlers.extend(
        handler
        for value in logging.Logger.manager.loggerDict.values()
        if isinstance(value, logging.Logger)
        for handler in value.handlers
    )
    streams: list[tuple[logging.StreamHandler, Any]] = []
    for handler in handlers:
        if isinstance(handler, logging.StreamHandler):
            streams.append((handler, handler.stream))
            handler.setStream(stderr)
    try:
        yield
    finally:
        for handler, stream in streams:
            handler.setStream(stream)


def create_actions_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/actions", tags=["actions"])

    @router.get("/catalog")
    def catalog():
        return {"actions": _catalog()}

    @router.post("/run")
    def run_action(request: ActionRequest):
        argv = request.argv
        if argv[0] not in _ALLOWED_TOP or argv[0] == "ui":
            raise HTTPException(status_code=400, detail="Unsupported CodeAnvil action")
        action_id = f"{argv[0]}.{argv[1]}" if argv[0] in {"mcp", "runtime"} and len(argv) > 1 else argv[0]
        if action_id in _BLOCKED or argv[0] in {"python", "sandbox"}:
            raise HTTPException(status_code=409, detail=_BLOCKED.get(action_id, "This action requires a live terminal."))
        if action_id in _CONFIRM and not request.confirm:
            raise HTTPException(status_code=428, detail="This action needs explicit confirmation")
        if argv[0] == "create" and not any(x == "--name" or (not x.startswith("-") and x != "create") for x in argv[1:]):
            raise HTTPException(status_code=400, detail="Provide a project name; interactive prompts are unavailable in the UI")
        if argv[0] == "telemetry":
            try:
                duration = float(argv[argv.index("--duration") + 1]) if "--duration" in argv else 0.0
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid telemetry duration")
            if duration <= 0 or duration > 3600:
                raise HTTPException(status_code=400, detail="UI telemetry runs must have a duration from 0.1 to 3600 seconds")
        try:
            cwd = _selected_cwd(root, request.project_path)
        except HTTPException:
            raise
        secrets: list[str] = []
        if argv[0] == "credential-setup":
            for i, item in enumerate(argv[:-1]):
                if item in {"--password", "-p", "--sudo-password", "-s"}:
                    secrets.append(argv[i + 1])
                elif item.startswith(("--password=", "--sudo-password=")):
                    secrets.append(item.split("=", 1)[1])
        stdout, stderr, code = io.StringIO(), io.StringIO(), 0
        previous_cwd = Path.cwd()
        with _CWD_LOCK:
            try:
                os.chdir(cwd)
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr), _capture_log_stream(stderr):
                    from codeanvil.CLI.parser import argparser
                    from codeanvil.CLI.main import choose_option
                    args = argparser(argv)
                    if getattr(args, "password", None) is None and argv[0] == "credential-setup":
                        raise HTTPException(status_code=400, detail="Enter the SSH password in the form")
                    choose_option(args)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
            except HTTPException:
                raise
            except BaseException as exc:
                code = 1
                stderr.write(f"{type(exc).__name__}: {exc}\n")
            finally:
                os.chdir(previous_cwd)
        return {
            "ok": code == 0,
            "exit_code": code,
            "stdout": _redact(stdout.getvalue(), secrets),
            "stderr": _redact(stderr.getvalue(), secrets),
        }

    return router
