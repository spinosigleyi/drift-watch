"""history command — list saved snapshots with metadata."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "history",
        help="List saved snapshots in a directory.",
    )
    p.add_argument(
        "--snapshot-dir",
        default=".drift_snapshots",
        help="Directory to scan for snapshot files (default: .drift_snapshots).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output history as JSON.",
    )
    p.set_defaults(func=run_history)


def _collect_snapshots(directory: str) -> list[dict]:
    """Return metadata for every *.json snapshot found in *directory*."""
    base = Path(directory)
    if not base.is_dir():
        return []

    entries: list[dict] = []
    for filepath in sorted(base.glob("*.json")):
        stat = filepath.stat()
        service_count: int | None = None
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                service_count = len(data)
        except (json.JSONDecodeError, OSError):
            pass

        entries.append(
            {
                "file": str(filepath),
                "size_bytes": stat.st_size,
                "modified": stat.st_mtime,
                "services": service_count,
            }
        )
    return entries


def run_history(args: argparse.Namespace) -> int:
    entries = _collect_snapshots(args.snapshot_dir)

    if not entries:
        print(f"No snapshots found in '{args.snapshot_dir}'.")
        return 0

    if args.as_json:
        print(json.dumps(entries, indent=2))
        return 0

    print(f"Snapshots in '{args.snapshot_dir}':")
    print(f"  {'FILE':<45} {'SERVICES':>8}  {'SIZE':>10}")
    print("  " + "-" * 67)
    for entry in entries:
        name = os.path.basename(entry["file"])
        svc = str(entry["services"]) if entry["services"] is not None else "?"
        size = f"{entry['size_bytes']} B"
        print(f"  {name:<45} {svc:>8}  {size:>10}")

    print(f"\n  Total: {len(entries)} snapshot(s).")
    return 0
