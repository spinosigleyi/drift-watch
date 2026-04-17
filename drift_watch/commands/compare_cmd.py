"""compare_cmd – diff two snapshots and report what changed between them."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Set

from drift_watch.snapshot import load_snapshot, SnapshotError


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "compare",
        help="Compare two snapshots and show configuration changes.",
    )
    p.add_argument("snapshot_a", help="Path to the older snapshot file.")
    p.add_argument("snapshot_b", help="Path to the newer snapshot file.")
    p.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Emit output as JSON.",
    )
    p.set_defaults(func=run_compare)


def _compare_snapshots(
    a: Dict[str, Any], b: Dict[str, Any]
) -> Dict[str, Any]:
    services_a: Set[str] = set(a.keys())
    services_b: Set[str] = set(b.keys())

    added = sorted(services_b - services_a)
    removed = sorted(services_a - services_b)
    changed: Dict[str, Dict[str, Any]] = {}

    for svc in sorted(services_a & services_b):
        cfg_a = a[svc]
        cfg_b = b[svc]
        if cfg_a != cfg_b:
            keys_a: Set[str] = set(cfg_a.keys())
            keys_b: Set[str] = set(cfg_b.keys())
            diff: Dict[str, Any] = {}
            for k in keys_a - keys_b:
                diff[k] = {"old": cfg_a[k], "new": None}
            for k in keys_b - keys_a:
                diff[k] = {"old": None, "new": cfg_b[k]}
            for k in keys_a & keys_b:
                if cfg_a[k] != cfg_b[k]:
                    diff[k] = {"old": cfg_a[k], "new": cfg_b[k]}
            if diff:
                changed[svc] = diff

    return {"added": added, "removed": removed, "changed": changed}


def run_compare(args: argparse.Namespace) -> int:
    try:
        snap_a = load_snapshot(Path(args.snapshot_a))
        snap_b = load_snapshot(Path(args.snapshot_b))
    except SnapshotError as exc:
        print(f"[error] {exc}")
        return 1

    result = _compare_snapshots(snap_a, snap_b)

    if args.as_json:
        print(json.dumps(result, indent=2))
        return 0

    if not result["added"] and not result["removed"] and not result["changed"]:
        print("No differences between snapshots.")
        return 0

    if result["added"]:
        print("Added services:")
        for s in result["added"]:
            print(f"  + {s}")
    if result["removed"]:
        print("Removed services:")
        for s in result["removed"]:
            print(f"  - {s}")
    if result["changed"]:
        print("Changed services:")
        for svc, diff in result["changed"].items():
            print(f"  ~ {svc}")
            for field, vals in diff.items():
                print(f"      {field}: {vals['old']!r} -> {vals['new']!r}")
    return 0
