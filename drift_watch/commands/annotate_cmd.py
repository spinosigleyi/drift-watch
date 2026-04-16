"""annotate_cmd – attach human-readable notes to a snapshot file."""
from __future__ import annotations

import json
from argparse import ArgumentParser, Namespace
from pathlib import Path

from drift_watch.snapshot import SnapshotError


def add_parser(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "annotate",
        help="Add or update a note on an existing snapshot.",
    )
    p.add_argument("snapshot", help="Path to the snapshot JSON file.")
    p.add_argument("--note", required=True, help="Annotation text to store.")
    p.add_argument(
        "--author", default="", help="Optional author name for the annotation."
    )
    p.set_defaults(func=run_annotate)


def _read_snapshot(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        raise SnapshotError(f"Snapshot not found: {path}")
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"Invalid JSON in snapshot: {exc}") from exc


def _write_snapshot(path: Path, data: dict) -> None:
    try:
        path.write_text(json.dumps(data, indent=2))
    except OSError as exc:
        raise SnapshotError(f"Cannot write snapshot: {exc}") from exc


def run_annotate(args: Namespace) -> int:
    path = Path(args.snapshot)
    try:
        data = _read_snapshot(path)
    except SnapshotError as exc:
        print(f"[annotate] error: {exc}")
        return 1

    annotation = {"note": args.note}
    if args.author:
        annotation["author"] = args.author

    data.setdefault("annotations", [])
    data["annotations"].append(annotation)

    try:
        _write_snapshot(path, data)
    except SnapshotError as exc:
        print(f"[annotate] error: {exc}")
        return 1

    print(f"[annotate] note added to {path}")
    return 0
