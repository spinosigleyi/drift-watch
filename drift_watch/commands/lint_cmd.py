"""lint_cmd – validate declared config files for common issues."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

from drift_watch.loader import load_declared_config, ConfigLoadError


def add_parser(subparsers) -> None:
    p = subparsers.add_parser("lint", help="Validate declared config files")
    p.add_argument("declared", help="Path to declared config (YAML/JSON)")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    p.set_defaults(func=run_lint)


def _lint_config(config: dict) -> List[Tuple[str, str]]:
    """Return list of (level, message) issues found in config."""
    issues: List[Tuple[str, str]] = []
    for service, fields in config.items():
        if not isinstance(fields, dict):
            issues.append(("error", f"{service}: value must be a mapping"))
            continue
        if not fields:
            issues.append(("warning", f"{service}: has no fields declared"))
        for key, val in fields.items():
            if val is None:
                issues.append(("warning", f"{service}.{key}: value is null"))
            if key != key.strip():
                issues.append(("error", f"{service}: key {key!r} has leading/trailing whitespace"))
    return issues


def run_lint(args: argparse.Namespace) -> int:
    try:
        config = load_declared_config(args.declared)
    except ConfigLoadError as exc:
        print(f"[error] {exc}")
        return 1

    issues = _lint_config(config)
    if not issues:
        print("OK – no issues found")
        return 0

    errors = 0
    for level, msg in issues:
        print(f"[{level}] {msg}")
        if level == "error":
            errors += 1

    warnings = len(issues) - errors
    print(f"\n{errors} error(s), {warnings} warning(s)")

    if errors or (args.strict and warnings):
        return 1
    return 0
