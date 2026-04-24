"""trend_cmd.py — show drift score trends over time across snapshots."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import List, Tuple


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'trend' subcommand."""
    p = subparsers.add_parser(
        "trend",
        help="show drift-score trend across historical snapshots",
    )
    p.add_argument(
        "--snapshot-dir",
        default=".drift_snapshots",
        metavar="DIR",
        help="directory containing snapshot JSON files (default: .drift_snapshots)",
    )
    p.add_argument(
        "--last",
        type=int,
        default=10,
        metavar="N",
        help="number of most-recent snapshots to include (default: 10)",
    )
    p.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="emit results as JSON instead of plain text",
    )
    p.set_defaults(func=run_trend)


def _snapshot_timestamp(path: Path) -> str:
    """Return the 'timestamp' field from a snapshot file, or '' on failure."""
    try:
        data = json.loads(path.read_text())
        return str(data.get("timestamp", ""))
    except Exception:  # noqa: BLE001
        return ""


def _collect_trend(
    snapshot_dir: str,
    last: int,
) -> List[Tuple[str, int, int, float]]:
    """Return a list of (timestamp, total, drifted, score) tuples.

    *score* is the percentage of services that are **not** drifted (0-100).
    Results are sorted oldest-first and capped at *last* entries.
    """
    directory = Path(snapshot_dir)
    if not directory.is_dir():
        return []

    files = sorted(
        directory.glob("*.json"),
        key=lambda p: _snapshot_timestamp(p),
    )
    # Take the N most recent
    files = files[-last:] if last > 0 else files

    rows: List[Tuple[str, int, int, float]] = []
    for path in files:
        try:
            data = json.loads(path.read_text())
        except Exception:  # noqa: BLE001
            continue

        timestamp = str(data.get("timestamp", path.stem))
        services = data.get("services", {})
        if not isinstance(services, dict):
            continue

        total = len(services)
        drifted = sum(
            1
            for svc in services.values()
            if isinstance(svc, dict) and svc.get("status") == "drifted"
        )
        score = round(100.0 * (total - drifted) / total, 1) if total else 100.0
        rows.append((timestamp, total, drifted, score))

    return rows


def run_trend(args: argparse.Namespace) -> int:
    """Entry point for the 'trend' subcommand."""
    rows = _collect_trend(
        snapshot_dir=args.snapshot_dir,
        last=args.last,
    )

    if args.json_output:
        output = [
            {"timestamp": ts, "total": total, "drifted": drifted, "score": score}
            for ts, total, drifted, score in rows
        ]
        print(json.dumps(output, indent=2))
        return 0

    if not rows:
        print("No snapshots found — nothing to trend.")
        return 0

    # Plain-text table
    header = f"{'TIMESTAMP':<30}  {'TOTAL':>6}  {'DRIFTED':>7}  {'SCORE':>6}"
    print(header)
    print("-" * len(header))
    for ts, total, drifted, score in rows:
        bar_len = int(score / 5)  # max 20 chars
        bar = "#" * bar_len + "." * (20 - bar_len)
        print(f"{ts:<30}  {total:>6}  {drifted:>7}  {score:>5.1f}%  [{bar}]")

    return 0
