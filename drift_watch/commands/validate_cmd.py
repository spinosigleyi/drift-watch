"""validate_cmd – check declared config files for structural correctness."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from drift_watch.loader import ConfigLoadError, load_declared_config


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "validate",
        help="Validate a declared config file for structural issues.",
    )
    p.add_argument("declared", help="Path to declared config YAML/JSON file.")
    p.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Treat warnings as errors.",
    )
    p.set_defaults(func=run_validate)


def _validate_structure(config: dict[str, Any]) -> list[dict[str, str]]:
    """Return a list of issue dicts with 'level' and 'message'."""
    issues: list[dict[str, str]] = []
    if not config:
        issues.append({"level": "warning", "message": "Declared config is empty."})
        return issues
    for service, fields in config.items():
        if not isinstance(fields, dict):
            issues.append(
                {
                    "level": "error",
                    "message": f"Service '{service}': value must be a mapping, got {type(fields).__name__}.",
                }
            )
            continue
        if not fields:
            issues.append(
                {"level": "warning", "message": f"Service '{service}' has no fields declared."}
            )
        for key, val in fields.items():
            if not str(key).strip():
                issues.append(
                    {"level": "error", "message": f"Service '{service}': blank field key found."}
                )
            if val is None:
                issues.append(
                    {
                        "level": "warning",
                        "message": f"Service '{service}': field '{key}' has a null value.",
                    }
                )
    return issues


def run_validate(args: argparse.Namespace) -> int:
    try:
        config = load_declared_config(args.declared)
    except ConfigLoadError as exc:
        print(f"[error] Failed to load declared config: {exc}", file=sys.stderr)
        return 1

    issues = _validate_structure(config)
    errors = [i for i in issues if i["level"] == "error"]
    warnings = [i for i in issues if i["level"] == "warning"]

    for issue in issues:
        prefix = "[error]" if issue["level"] == "error" else "[warn] "
        print(f"{prefix} {issue['message']}")

    if not issues:
        print(f"OK  {args.declared} — no issues found.")

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0
