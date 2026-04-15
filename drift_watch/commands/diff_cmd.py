"""diff command: compare a live config against a saved snapshot."""
from __future__ import annotations

import argparse
from typing import Any, Dict

from drift_watch.detector import detect_drift
from drift_watch.reporter import format_text_report, format_json_report
from drift_watch.snapshot import load_snapshot, SnapshotError
from drift_watch.loader import load_live_config, ConfigLoadError


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'diff' sub-command."""
    p = subparsers.add_parser(
        "diff",
        help="Compare live config against a saved snapshot.",
    )
    p.add_argument("snapshot", help="Path to a snapshot JSON file.")
    p.add_argument("live", help="Path to the live config YAML/JSON file.")
    p.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        default=False,
        help="Emit results as JSON.",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 when drift is detected.",
    )
    p.set_defaults(func=run_diff)


def run_diff(args: argparse.Namespace) -> int:
    """Execute the diff command.  Returns an exit code."""
    # Load snapshot (declared baseline)
    try:
        declared: Dict[str, Any] = load_snapshot(args.snapshot)
    except SnapshotError as exc:
        print(f"[diff] snapshot error: {exc}")
        return 1

    # Load live config
    try:
        live: Dict[str, Any] = load_live_config(args.live)
    except ConfigLoadError as exc:
        print(f"[diff] live config error: {exc}")
        return 1

    reports = detect_drift(declared, live)

    if args.json_output:
        print(format_json_report(reports))
    else:
        print(format_text_report(reports))

    if args.exit_code:
        from drift_watch.models import DriftStatus
        drifted = any(
            r.status in (DriftStatus.DRIFTED, DriftStatus.MISSING)
            for r in reports
        )
        return 1 if drifted else 0

    return 0
