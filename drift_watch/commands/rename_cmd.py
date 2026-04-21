"""rename_cmd – rename a service key across all snapshots in a directory."""
from __future__ import annotations

import json
import os
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import List, Tuple


def add_parser(subparsers) -> None:
    """Register the 'rename' subcommand."""
    p: ArgumentParser = subparsers.add_parser(
        "rename",
        help="Rename a service key across all snapshots.",
    )
    p.add_argument("old_name", help="Current service name to rename.")
    p.add_argument("new_name", help="New service name.")
    p.add_argument(
        "--snapshot-dir",
        default="snapshots",
        help="Directory that contains snapshot JSON files (default: snapshots).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without modifying files.",
    )
    p.set_defaults(func=run_rename)


def _rename_in_snapshot(
    path: Path, old_name: str, new_name: str
) -> bool:
    """Load *path*, rename *old_name* → *new_name* in services dict.

    Returns True when the file was (or would be) modified.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False

    services = data.get("services")
    if not isinstance(services, dict) or old_name not in services:
        return False

    services[new_name] = services.pop(old_name)
    data["services"] = services
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return True


def run_rename(args: Namespace) -> int:
    """Entry-point for the rename subcommand."""
    snapshot_dir = Path(args.snapshot_dir)

    if not snapshot_dir.is_dir():
        print(f"[rename] snapshot directory not found: {snapshot_dir}")
        return 0

    files: List[Path] = sorted(snapshot_dir.glob("*.json"))
    if not files:
        print("[rename] no snapshot files found.")
        return 0

    modified: List[Path] = []
    for snap_path in files:
        if args.dry_run:
            # Peek without writing
            try:
                data = json.loads(snap_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            services = data.get("services", {})
            if isinstance(services, dict) and args.old_name in services:
                modified.append(snap_path)
        else:
            if _rename_in_snapshot(snap_path, args.old_name, args.new_name):
                modified.append(snap_path)

    prefix = "[dry-run] would update" if args.dry_run else "[rename] updated"
    for p in modified:
        print(f"{prefix}: {p}")

    if not modified:
        print(f"[rename] service '{args.old_name}' not found in any snapshot.")
    else:
        print(
            f"[rename] '{args.old_name}' → '{args.new_name}' "
            f"in {len(modified)} snapshot(s)."
        )
    return 0
