"""stats command – aggregate drift statistics across all snapshots."""
from __future__ import annotations

import json
import pathlib
from argparse import ArgumentParser, Namespace
from typing import Dict, Any


def add_parser(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "stats", help="Show aggregate drift statistics from snapshot history"
    )
    p.add_argument(
        "--snapshot-dir",
        default=".drift_snapshots",
        help="Directory containing snapshot files (default: .drift_snapshots)",
    )
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output statistics as JSON",
    )
    p.set_defaults(func=run_stats)


def _aggregate(snapshot_dir: str) -> Dict[str, Any]:
    directory = pathlib.Path(snapshot_dir)
    if not directory.exists():
        return {"snapshots": 0, "total_services": 0, "drifted_services": 0, "drift_rate": 0.0}

    snapshots = sorted(directory.glob("*.json"))
    total_snapshots = len(snapshots)
    total_services = 0
    drifted_services = 0

    for path in snapshots:
        try:
            data = json.loads(path.read_text())
            services = data.get("services", {})
            for _name, fields in services.items():
                total_services += 1
                if any(f.get("drifted") for f in fields.values() if isinstance(f, dict)):
                    drifted_services += 1
        except (json.JSONDecodeError, AttributeError):
            continue

    rate = round(drifted_services / total_services, 4) if total_services else 0.0
    return {
        "snapshots": total_snapshots,
        "total_services": total_services,
        "drifted_services": drifted_services,
        "drift_rate": rate,
    }


def run_stats(args: Namespace) -> int:
    stats = _aggregate(args.snapshot_dir)

    if args.as_json:
        print(json.dumps(stats, indent=2))
    else:
        print(f"Snapshots analysed : {stats['snapshots']}")
        print(f"Total services     : {stats['total_services']}")
        print(f"Drifted services   : {stats['drifted_services']}")
        print(f"Drift rate         : {stats['drift_rate']:.2%}")

    return 0
