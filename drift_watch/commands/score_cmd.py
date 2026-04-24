"""score_cmd – compute a drift health score across snapshots.

The score is a float in [0.0, 100.0] where 100 means zero drift across
all services in every snapshot found in the snapshot directory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Tuple


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "score",
        help="compute a drift health score across all snapshots",
    )
    p.add_argument(
        "--snapshot-dir",
        default=".drift_snapshots",
        help="directory containing snapshot JSON files (default: .drift_snapshots)",
    )
    p.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        default=False,
        help="emit result as JSON",
    )
    p.set_defaults(func=run_score)


def _aggregate(snapshot_dir: Path) -> Tuple[int, int]:
    """Return (total_services, drifted_services) across all snapshots."""
    total = 0
    drifted = 0
    if not snapshot_dir.is_dir():
        return total, drifted
    for snap_file in sorted(snapshot_dir.glob("*.json")):
        try:
            data = json.loads(snap_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        services = data.get("services", {})
        if not isinstance(services, dict):
            continue
        for svc_data in services.values():
            if not isinstance(svc_data, dict):
                continue
            total += 1
            if svc_data.get("status") == "drifted":
                drifted += 1
    return total, drifted


def _compute_score(total: int, drifted: int) -> float:
    if total == 0:
        return 100.0
    return round((total - drifted) / total * 100.0, 2)


def run_score(args: argparse.Namespace) -> int:
    snapshot_dir = Path(args.snapshot_dir)
    total, drifted = _aggregate(snapshot_dir)
    score = _compute_score(total, drifted)

    if args.json_output:
        import sys
        print(
            json.dumps(
                {"score": score, "total_services": total, "drifted_services": drifted},
                indent=2,
            ),
            file=sys.stdout,
        )
    else:
        ok = total - drifted
        print(f"Drift health score : {score:.2f} / 100")
        print(f"Services checked   : {total}")
        print(f"  OK               : {ok}")
        print(f"  Drifted          : {drifted}")

    return 0
