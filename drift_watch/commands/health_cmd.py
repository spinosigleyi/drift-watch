"""health_cmd – summarise service health across the latest snapshot.

Exits 0 when all services are healthy (no drift), 1 otherwise.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def add_parser(subparsers: Any) -> None:  # pragma: no cover – wired in __init__
    p = subparsers.add_parser(
        "health",
        help="Show health status of services from the latest snapshot.",
    )
    p.add_argument(
        "--snapshot-dir",
        default=".drift_snapshots",
        help="Directory containing snapshots (default: .drift_snapshots).",
    )
    p.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit results as JSON.",
    )
    p.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit 1 when any service has drifted.",
    )
    p.set_defaults(func=run_health)


def _latest_snapshot(snapshot_dir: Path) -> dict[str, Any] | None:
    """Return the parsed contents of the most-recently modified snapshot file."""
    candidates = sorted(
        snapshot_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None
    with candidates[0].open() as fh:
        return json.load(fh)  # type: ignore[no-any-return]


def _collect_health(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a health record for each service stored in *data*."""
    services: dict[str, Any] = data.get("services", {})
    records: list[dict[str, Any]] = []
    for name, info in services.items():
        status = info.get("status", "unknown") if isinstance(info, dict) else "unknown"
        records.append({"service": name, "status": status})
    return records


def run_health(args: Any) -> int:
    snapshot_dir = Path(args.snapshot_dir)
    if not snapshot_dir.is_dir():
        print(f"[health] snapshot directory not found: {snapshot_dir}", file=sys.stderr)
        return 0

    data = _latest_snapshot(snapshot_dir)
    if data is None:
        print("[health] no snapshots found.", file=sys.stderr)
        return 0

    records = _collect_health(data)
    drifted = [r for r in records if r["status"] != "ok"]

    if getattr(args, "json_output", False):
        print(json.dumps({"services": records, "drifted_count": len(drifted)}, indent=2))
    else:
        for r in records:
            indicator = "✓" if r["status"] == "ok" else "✗"
            print(f"  {indicator}  {r['service']}  [{r['status']}]")
        print(f"\n{len(records)} service(s) checked, {len(drifted)} drifted.")

    if getattr(args, "fail_on_drift", False) and drifted:
        return 1
    return 0
