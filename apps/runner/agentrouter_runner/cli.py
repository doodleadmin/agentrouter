"""Argparse CLI for Local Runner skeleton."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import RunnerConfig
from .paths import PathOutsideRootError, RootValidationError, resolve_requested_path, safe_relative_path
from .safety import classify_path, explain_safety_flags
from .status import build_status


def _render(payload: dict[str, object], json_output: bool) -> str:
    if json_output:
        return json.dumps(payload, indent=2, sort_keys=True)
    lines = [f"{k}: {v}" for k, v in payload.items()]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentrouter-runner", description="Local Runner skeleton CLI")
    parser.add_argument("--json", action="store_true", dest="json_output", help="JSON output")
    parser.add_argument("--root", default=".", help="Allowed root path (default: current directory)")

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Show runner skeleton status")
    sub.add_parser("doctor", help="Run local safe checks")

    check_path = sub.add_parser("check-path", help="Validate requested path against allowed root")
    check_path.add_argument("--path", required=True, dest="requested", help="Requested path")

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = RunnerConfig(root=Path(args.root), json_output=args.json_output)

    if args.command == "status":
        payload = build_status(config.root).to_dict()
        print(_render(payload, config.json_output))
        return 0

    if args.command == "doctor":
        status = build_status(config.root)
        payload: dict[str, object] = {
            "runner_mode": status.runner_mode,
            "root": status.root,
            "root_exists": status.root_exists,
            "root_is_dir": status.root_is_dir,
            "root_valid": status.root_valid,
            "cloud_connection": "disabled",
            "command_execution": "disabled",
            "overall": "ok" if status.root_valid else "fail",
        }
        print(_render(payload, config.json_output))
        return 0 if status.root_valid else 1

    if args.command == "check-path":
        try:
            resolved = resolve_requested_path(config.root, args.requested)
            flags = classify_path(resolved)
            payload = {
                "allowed": True,
                "root": str(Path(config.root).resolve(strict=False)),
                "requested": args.requested,
                "resolved": str(resolved),
                "relative": safe_relative_path(config.root, resolved),
                "flags": flags,
                "safety_notes": explain_safety_flags(flags),
            }
            print(_render(payload, config.json_output))
            return 0
        except (RootValidationError, PathOutsideRootError) as exc:
            payload = {
                "allowed": False,
                "requested": args.requested,
                "error": type(exc).__name__,
                "message": str(exc),
            }
            print(_render(payload, config.json_output))
            return 2

    parser.error("Unknown command")
    return 2
