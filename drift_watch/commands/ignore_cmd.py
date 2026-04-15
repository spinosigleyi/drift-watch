"""ignore_cmd – manage a drift-ignore file (.driftignore).

The ignore file is a simple JSON list of glob patterns.  Any ConfigField
whose key matches one of the patterns is excluded from drift reports.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
from typing import List

DEFAULT_IGNORE_FILE = ".driftignore"


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "ignore",
        help="manage .driftignore patterns (add / list / remove)",
    )
    p.add_argument(
        "--file",
        default=DEFAULT_IGNORE_FILE,
        metavar="PATH",
        help="path to the ignore file (default: .driftignore)",
    )
    sub = p.add_subparsers(dest="ignore_action", required=True)

    add = sub.add_parser("add", help="add a pattern")
    add.add_argument("pattern", help="glob pattern to ignore, e.g. 'env.*'")

    sub.add_parser("list", help="list current patterns")

    rm = sub.add_parser("remove", help="remove a pattern")
    rm.add_argument("pattern", help="pattern to remove")

    p.set_defaults(func=run_ignore)


def _load(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    return [str(p) for p in data]


def _save(path: str, patterns: List[str]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(sorted(set(patterns)), fh, indent=2)
        ")


def is_ignored(field_key: str, patterns: List[str]) -> bool:
    """Return True if *field_key* matches any pattern in *patterns*."""
    return any(fnmatch.fnmatch(field_key, p) for p in patterns)


def run_ignore(args: argparse.Namespace) -> int:
    path = args.file
    try:
        patterns = _load(path)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    action = args.ignore_action

    if action == "list":
        if not patterns:
            print("(no patterns)")
        else:
            for pat in patterns:
                print(pat)
        return 0

    if action == "add":
        if args.pattern in patterns:
            print(f"pattern already present: {args.pattern}")
            return 0
        patterns.append(args.pattern)
        _save(path, patterns)
        print(f"added: {args.pattern}")
        return 0

    if action == "remove":
        if args.pattern not in patterns:
            print(f"pattern not found: {args.pattern}", file=sys.stderr)
            return 1
        patterns.remove(args.pattern)
        _save(path, patterns)
        print(f"removed: {args.pattern}")
        return 0

    print(f"unknown action: {action}", file=sys.stderr)
    return 1
