"""report_cmd – generate a consolidated drift report across all snapshots."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from drift_watch.snapshot import load_snapshot, SnapshotError


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("report", help="Generate a consolidated drift report")
    p.add_argument(
        "--snapshot-dir",
        default="snapshots",
        help="Directory containing snapshot JSON files (default: snapshots)",
    )
    p.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--out-file",
        default=None,
        help="Write output to this file instead of stdout",
    )
    p.set_defaults(func=run_report)


def _collect_report(snapshot_dir: str) -> dict[str, Any]:
    """Aggregate drift statistics across all snapshots in *snapshot_dir*."""
    directory = Path(snapshot_dir)
    if not directory.is_dir():
        return {"snapshots": 0, "services": {}, "total_drifted": 0}

    services: dict[str, dict[str, Any]] = {}
    snapshot_count = 0

    for path in sorted(directory.glob("*.json")):
        try:
            data = load_snapshot(str(path))
        except SnapshotError:
            continue
        snapshot_count += 1
        for svc_name, svc_data in data.items():
            entry = services.setdefault(
                svc_name,
                {"drift_count": 0, "ok_count": 0, "appearances": 0},
            )
            entry["appearances"] += 1
            status = svc_data.get("status", "ok") if isinstance(svc_data, dict) else "ok"
            if status in ("drifted", "missing"):
                entry["drift_count"] += 1
            else:
                entry["ok_count"] += 1

    total_drifted = sum(1 for s in services.values() if s["drift_count"] > 0)
    return {
        "snapshots": snapshot_count,
        "services": services,
        "total_drifted": total_drifted,
    }


def _format_text(data: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"Snapshots scanned : {data['snapshots']}")
    lines.append(f"Services tracked  : {len(data['services'])}")
    lines.append(f"Services w/ drift : {data['total_drifted']}")
    if data["services"]:
        lines.append("")
        lines.append(f"{'Service':<30} {'Appearances':>11} {'Drifted':>7} {'OK':>5}")
        lines.append("-" * 57)
        for name, info in sorted(data["services"].items()):
            lines.append(
                f"{name:<30} {info['appearances']:>11} {info['drift_count']:>7} {info['ok_count']:>5}"
            )
    return "\n".join(lines)


def run_report(args: argparse.Namespace) -> int:
    data = _collect_report(args.snapshot_dir)

    if args.output == "json":
        content = json.dumps(data, indent=2)
    else:
        content = _format_text(data)

    if args.out_file:
        try:
            Path(args.out_file).write_text(content + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot write to {args.out_file}: {exc}", file=sys.stderr)
            return 1
    else:
        print(content)

    return 0
