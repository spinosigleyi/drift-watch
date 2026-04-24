"""trend_cmd: show drift rate trends across snapshot history."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_SNAPSHOT_DIR = "snapshots"


def add_parser(subparsers: Any) -> None:
    p = subparsers.add_parser("trend", help="Show drift rate trend over time")
    p.add_argument(
        "--snapshot-dir",
        default=DEFAULT_SNAPSHOT_DIR,
        help="Directory containing snapshots (default: snapshots)",
    )
    p.add_argument(
        "--last",
        type=int,
        default=10,
        metavar="N",
        help="Consider only the N most recent snapshots (default: 10)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON",
    )
    p.set_defaults(func=run_trend)


def _snapshot_timestamp(path: Path) -> datetime:
    """Return the captured_at timestamp from a snapshot file, or epoch on error."""
    try:
        data = json.loads(path.read_text())
        ts = data.get("captured_at", "")
        return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.fromtimestamp(0, tz=timezone.utc)


def _collect_trend(snapshot_dir: str, last: int) -> list[dict[str, Any]]:
    """Return a list of {timestamp, total, drifted, drift_rate} dicts."""
    base = Path(snapshot_dir)
    if not base.is_dir():
        return []

    files = sorted(base.glob("*.json"), key=_snapshot_timestamp)
    files = files[-last:]

    points: list[dict[str, Any]] = []
    for f in files:
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        services = data.get("services", {})
        total = len(services)
        drifted = sum(
            1
            for svc in services.values()
            if isinstance(svc, dict) and svc.get("status") == "drifted"
        )
        drift_rate = round(drifted / total, 4) if total else 0.0
        points.append(
            {
                "timestamp": data.get("captured_at", f.stem),
                "total": total,
                "drifted": drifted,
                "drift_rate": drift_rate,
            }
        )
    return points


def run_trend(args: Any) -> int:
    points = _collect_trend(args.snapshot_dir, args.last)

    if not points:
        print("No snapshots found.")
        return 0

    if args.json:
        print(json.dumps(points, indent=2))
        return 0

    header = f"{'Timestamp':<30} {'Total':>6} {'Drifted':>8} {'Rate':>7}"
    print(header)
    print("-" * len(header))
    for pt in points:
        print(
            f"{pt['timestamp']:<30} {pt['total']:>6} {pt['drifted']:>8} "
            f"{pt['drift_rate']:>7.2%}"
        )
    return 0
