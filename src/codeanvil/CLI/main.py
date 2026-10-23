"""Subcommand dispatch and console-script entry point."""

import argparse

from codeanvil.CLI.commands import (
    cmd_create,
    cmd_init,
    cmd_list,
    cmd_now,
    cmd_sandbox,
    cmd_status,
    cmd_sync,
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
        case "now":
            cmd_now(tz=args.tz, machine=args.machine)
        case "sandbox":
            cmd_sandbox(args.agent)


def main() -> None:
    """Console-script entry point (`codeanvil ...`)."""
    choose_option(argparser())
