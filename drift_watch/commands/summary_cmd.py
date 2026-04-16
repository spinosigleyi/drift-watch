"""summary command – print an aggregated drift summary across all snapshots."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from drift_watch.commands.history_cmd import _collect_snapshots


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "summary",
        help="Show aggregated drift statistics across saved snapshots.",
    )
    p.add_argument(
        "--snapshot-dir",
        default=".drift_watch/snapshots",
        help="Directory containing snapshot files (default: .drift_watch/snapshots).",
    )
    p.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="Show the N most frequently drifted services (default: 5).",
    )
    p.set_defaults(func=run_summary)


def _count_drift(snapshots: List[dict]) -> dict[str, int]:
    """Return a mapping of service_name -> drift occurrence count."""
    counts: dict[str, int] = {}
    for snap in snapshots:
        for service, data in snap.get("services", {}).items():
            status = data.get("status", "")
            if status in ("drifted", "missing"):
                counts[service] = counts.get(service, 0) + 1
    return counts


def run_summary(args: argparse.Namespace) -> int:
    snapshot_dir = Path(args.snapshot_dir)
    snapshots = _collect_snapshots(snapshot_dir)

    if not snapshots:
        print("No snapshots found.")
        return 0

    counts = _count_drift(snapshots)
    total_snaps = len(snapshots)
    total_services = sum(
        len(s.get("services", {})) for s in snapshots
    )
    drifted_total = sum(counts.values())

    print(f"Snapshots analysed : {total_snaps}")
    print(f"Service-checks     : {total_services}")
    print(f"Drift occurrences  : {drifted_total}")

    if counts:
        top_n = sorted(counts.items(), key=lambda x: x[1], reverse=True)[: args.top]
        print(f"\nTop {args.top} most drifted services:")
        for rank, (svc, cnt) in enumerate(top_n, 1):
            print(f"  {rank}. {svc}  ({cnt} time{'s' if cnt != 1 else ''})")
    else:
        print("No drift detected across all snapshots.")

    return 0
