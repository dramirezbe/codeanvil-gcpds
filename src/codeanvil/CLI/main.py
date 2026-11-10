"""Subcommand dispatch and console-script entry point."""

import argparse

from codeanvil.CLI.commands import (
    cmd_backup,
    cmd_create,
    cmd_init,
    cmd_list,
    cmd_mcp,
    cmd_now,
    cmd_python,
    cmd_runtime,
    cmd_sandbox,
    cmd_status,
    cmd_sync,
    cmd_telemetry,
    cmd_upgrade,
)
from codeanvil.CLI.parser import argparser


def choose_option(args: argparse.Namespace) -> None:
    match args.command:
        case "init":
            cmd_init(mcp_servers=args.mcp_servers or None)
        case "create":
            cmd_create(
                args.name,
                args.path,
                mcp_servers=args.mcp_servers or None,
                project_name=args.project_name,
                folder=args.folder,
            )
        case "list":
            cmd_list()
        case "sync":
            cmd_sync()
        case "status":
            cmd_status(args.name)
        case "backup":
            cmd_backup(args.stage)
        case "runtime":
            cmd_runtime(args.action, getattr(args, "packages", None))
        case "mcp":
            cmd_mcp(args.action, getattr(args, "names", None), getattr(args, "yes", False))
        case "python":
            cmd_python(args.script, args.args)
        case "now":
            cmd_now(tz=args.tz, machine=args.machine)
        case "sandbox":
            cmd_sandbox(args.agent)
        case "telemetry":
            cmd_telemetry(
                pid=args.pid,
                output=args.output,
                interval=args.interval,
                duration=args.duration,
                counters=args.counters,
            )
        case "upgrade":
            cmd_upgrade()


def main() -> None:
    """Console-script entry point (`codeanvil ...`)."""
    choose_option(argparser())
