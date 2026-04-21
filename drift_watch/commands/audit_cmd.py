"""audit_cmd – show a per-service audit trail from snapshot history."""
from __future__ import annotations

import json
import os
from argparse import ArgumentParser, Namespace
from typing import List, Dict, Any

DEFAULT_SNAPSHOT_DIR = "snapshots"


def add_parser(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "audit",
        help="Show audit trail for a service across snapshots.",
    )
    p.add_argument("service", help="Service name to audit.")
    p.add_argument(
        "--snapshot-dir",
        default=DEFAULT_SNAPSHOT_DIR,
        help="Directory containing snapshot files (default: snapshots).",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of snapshots to include (default: 10).",
    )
    p.set_defaults(func=run_audit)


def _collect_audit_entries(
    snapshot_dir: str, service: str, limit: int
) -> List[Dict[str, Any]]:
    """Return audit entries for *service* from the most-recent snapshots."""
    if not os.path.isdir(snapshot_dir):
        return []

    files = sorted(
        [
            f
            for f in os.listdir(snapshot_dir)
            if f.endswith(".json")
        ],
        reverse=True,
    )[:limit]

    entries: List[Dict[str, Any]] = []
    for filename in files:
        path = os.path.join(snapshot_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError):
            continue

        services = data.get("services", {})
        if service in services:
            entries.append(
                {
                    "snapshot": filename,
                    "timestamp": data.get("timestamp", "unknown"),
                    "config": services[service],
                }
            )
    return entries


def run_audit(args: Namespace) -> int:
    entries = _collect_audit_entries(
        args.snapshot_dir, args.service, args.limit
    )

    if not entries:
        print(f"No audit history found for service '{args.service}'.")
        return 0

    print(f"Audit trail for '{args.service}' ({len(entries)} snapshot(s)):")
    for entry in entries:
        print(f"  [{entry['timestamp']}] {entry['snapshot']}")
        for key, value in entry["config"].items():
            print(f"    {key}: {value}")
    return 0
