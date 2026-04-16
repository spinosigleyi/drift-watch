"""prune_cmd – remove snapshot files older than N days."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "prune",
        help="Delete snapshots older than a given number of days.",
    )
    p.add_argument(
        "--snapshot-dir",
        default=".drift_snapshots",
        help="Directory that contains snapshot JSON files (default: .drift_snapshots).",
    )
    p.add_argument(
        "--older-than",
        type=int,
        default=30,
        dest="older_than",
        help="Remove snapshots whose 'timestamp' is older than this many days (default: 30).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print files that would be removed without deleting them.",
    )
    p.set_defaults(func=run_prune)


def _snapshot_timestamp(path: Path) -> datetime | None:
    """Return the UTC datetime stored in a snapshot file, or None on failure."""
    try:
        data = json.loads(path.read_text())
        ts = data.get("timestamp")
        if ts is None:
            return None
        return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def run_prune(args: argparse.Namespace) -> int:
    snapshot_dir = Path(args.snapshot_dir)
    if not snapshot_dir.is_dir():
        print(f"[prune] Directory not found: {snapshot_dir}")
        return 0

    cutoff = datetime.now(tz=timezone.utc).timestamp() - args.older_than * 86400
    removed = 0

    for snap_file in sorted(snapshot_dir.glob("*.json")):
        ts = _snapshot_timestamp(snap_file)
        if ts is None:
            continue
        if ts.timestamp() < cutoff:
            if args.dry_run:
                print(f"[prune] Would remove: {snap_file}")
            else:
                snap_file.unlink()
                print(f"[prune] Removed: {snap_file}")
            removed += 1

    label = "Would remove" if args.dry_run else "Removed"
    print(f"[prune] {label} {removed} snapshot(s).")
    return 0
