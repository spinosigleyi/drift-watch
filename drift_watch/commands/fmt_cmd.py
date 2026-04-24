"""fmt_cmd: normalize and reformat snapshot files to canonical JSON."""
from __future__ import annotations

import json
import pathlib
import sys
from argparse import ArgumentParser, _SubParsersAction
from typing import Any


def add_parser(subparsers: _SubParsersAction) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser(
        "fmt",
        help="Reformat snapshot JSON files to canonical pretty-printed form.",
    )
    p.add_argument(
        "--snapshot-dir",
        default="snapshots",
        metavar="DIR",
        help="Directory containing snapshot files (default: snapshots).",
    )
    p.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Exit non-zero if any file would be reformatted without writing.",
    )
    p.add_argument(
        "--indent",
        type=int,
        default=2,
        metavar="N",
        help="JSON indentation level (default: 2).",
    )
    p.set_defaults(func=run_fmt)


def _canonical(data: Any, indent: int) -> str:
    """Return canonical JSON string for *data*."""
    return json.dumps(data, indent=indent, sort_keys=True, ensure_ascii=False) + "\n"


def run_fmt(args: Any) -> int:
    snapshot_dir = pathlib.Path(args.snapshot_dir)
    if not snapshot_dir.exists():
        print(f"[fmt] snapshot directory not found: {snapshot_dir}", file=sys.stderr)
        return 1

    files = sorted(snapshot_dir.glob("*.json"))
    if not files:
        print("[fmt] no snapshot files found.")
        return 0

    needs_format: list[pathlib.Path] = []
    errors: list[str] = []

    for path in files:
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
            continue

        canonical = _canonical(data, args.indent)
        if raw != canonical:
            needs_format.append(path)
            if not args.check:
                path.write_text(canonical, encoding="utf-8")
                print(f"[fmt] reformatted {path.name}")
            else:
                print(f"[fmt] would reformat {path.name}")

    for err in errors:
        print(f"[fmt] error: {err}", file=sys.stderr)

    if errors:
        return 1
    if args.check and needs_format:
        return 1
    if not needs_format:
        print(f"[fmt] {len(files)} file(s) already canonical.")
    return 0
