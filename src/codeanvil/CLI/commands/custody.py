"""Command: codeanvil custody — file/tree hashing and verification."""

import sys
from pathlib import Path

from codeanvil.custody import file_sha256, tree_sha256, verify, verify_manifest
from codeanvil.config.logger import get_logger

log = get_logger(__name__)


def _format_input_line(path: str, sha256: str) -> str:
    """Format as ready-to-paste Input: line."""
    return f"Input: {path} sha256:{sha256}"


def cmd_custody(args) -> int:
    """Dispatch to custody subcommands."""
    if not args.subcommand or args.subcommand == "help":
        print("Usage: codeanvil custody <digest|verify|verify-manifest> [options]")
        print("  digest <path...>          Compute SHA-256; directories end with /")
        print("  verify [--cycle CYCLE]    Check Input: digests in reports")
        print("  verify-manifest <file>    Check golden vector manifest against vectors")
        return 0
    
    if args.subcommand == "digest":
        return cmd_digest(args)
    elif args.subcommand == "verify":
        return cmd_verify(args)
    elif args.subcommand == "verify-manifest":
        return cmd_verify_manifest(args)
    else:
        log.error("unknown custody subcommand: %s", args.subcommand)
        return 1


def cmd_digest(args) -> int:
    """Compute SHA-256 digests: `codeanvil custody digest <path...>`"""
    if not args.paths:
        log.error("digest requires at least one path")
        return 2
    
    exit_code = 0
    for path_str in args.paths:
        path = Path(path_str)
        
        # Normalize: directory paths end with /
        is_dir_requested = path_str.endswith("/") or path_str.endswith("\\")
        
        if not path.exists():
            log.error("path not found: %s", path)
            exit_code = 2
            continue
        
        if path.is_dir() or is_dir_requested:
            sha = tree_sha256(path)
            norm_path = str(path).rstrip("/").rstrip("\\") + "/"
        else:
            sha = file_sha256(path)
            norm_path = str(path)
        
        if args.raw:
            print(sha)
        else:
            print(_format_input_line(norm_path, sha))
    
    return exit_code


def cmd_verify(args) -> int:
    """Verify report digests: `codeanvil custody verify [--cycle CYCLE]`"""
    findings = verify(Path.cwd(), args.cycle, getattr(args, "gate", None))
    
    if not findings:
        return 0
    
    for finding in findings:
        print(f"{finding.kind}: {finding.path}")
        if finding.recorded:
            print(f"  recorded: {finding.recorded}")
        if finding.current:
            print(f"  current:  {finding.current}")
    
    return 1


def cmd_verify_manifest(args) -> int:
    """Verify golden manifest: `codeanvil custody verify-manifest <file>`"""
    if not args.manifest:
        log.error("verify-manifest requires a manifest file path")
        return 2
    
    manifest_path = Path(args.manifest)
    findings = verify_manifest(manifest_path)
    
    if not findings:
        return 0
    
    for finding in findings:
        print(f"{finding.kind}: {finding.path}")
        if finding.recorded:
            print(f"  recorded: {finding.recorded}")
        if finding.current:
            print(f"  current:  {finding.current}")
    
    return 1
