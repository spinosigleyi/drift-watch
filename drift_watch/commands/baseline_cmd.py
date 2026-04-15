"""baseline_cmd — mark current live config as the accepted baseline.

Saves a snapshot tagged as a baseline so future drift comparisons
can optionally be made against it instead of the declared IaC state.
"""
from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path

from drift_watch.loader import ConfigLoadError, load_live_config
from drift_watch.snapshot import SnapshotError, save_snapshot

_BASELINE_META_KEY = "__baseline__"


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "baseline",
        help="Capture live config as the accepted baseline.",
    )
    p.add_argument(
        "live",
        metavar="LIVE_CONFIG",
        help="Path to the live-config YAML/JSON file.",
    )
    p.add_argument(
        "--output",
        "-o",
        default=".drift_watch/baseline.json",
        metavar="PATH",
        help="Destination file for the baseline snapshot (default: %(default)s).",
    )
    p.add_argument(
        "--note",
        default="",
        metavar="TEXT",
        help="Optional human-readable note stored inside the baseline file.",
    )


def run_baseline(args: argparse.Namespace) -> int:
    """Execute the baseline sub-command.  Returns exit code."""
    try:
        services = load_live_config(args.live)
    except ConfigLoadError as exc:
        print(f"[baseline] ERROR loading live config: {exc}")
        return 1

    # Attach baseline metadata so the file can be distinguished from a
    # regular snapshot when loaded later.
    meta: dict = {
        _BASELINE_META_KEY: {
            "captured_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "source": str(args.live),
            "note": args.note,
        }
    }
    payload = {**meta, **services}

    try:
        save_snapshot(payload, args.output)
    except SnapshotError as exc:
        print(f"[baseline] ERROR saving baseline: {exc}")
        return 1

    service_count = len(services)
    print(
        f"[baseline] Baseline saved → {args.output} "
        f"({service_count} service{'s' if service_count != 1 else ''})"
    )
    return 0
