"""CLI sub-command: snapshot

Captures the current live configuration to a snapshot file so it can
later be used as the *declared* baseline for drift detection.
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace

from drift_watch.loader import ConfigLoadError, load_live_config
from drift_watch.snapshot import SnapshotError, save_snapshot


def add_parser(subparsers) -> None:  # type: ignore[type-arg]
    """Register the ``snapshot`` sub-command on *subparsers*."""
    p: ArgumentParser = subparsers.add_parser(
        "snapshot",
        help="Capture the live configuration to a snapshot file.",
    )
    p.add_argument(
        "live",
        metavar="LIVE_CONFIG",
        help="Path to the live-config YAML/JSON file (or directory of files).",
    )
    p.add_argument(
        "--output",
        "-o",
        metavar="SNAPSHOT_FILE",
        default="drift_snapshot.json",
        help="Destination snapshot file (default: drift_snapshot.json).",
    )
    p.set_defaults(func=run_snapshot)


def run_snapshot(args: Namespace) -> int:
    """Execute the snapshot sub-command.

    Returns:
        0 on success, 1 on error.
    """
    try:
        live_config = load_live_config(args.live)
    except ConfigLoadError as exc:
        print(f"drift-watch snapshot: error loading live config: {exc}", file=sys.stderr)
        return 1

    try:
        save_snapshot(live_config, args.output)
    except SnapshotError as exc:
        print(f"drift-watch snapshot: {exc}", file=sys.stderr)
        return 1

    service_count = len(live_config)
    noun = "service" if service_count == 1 else "services"
    print(f"Snapshot saved to {args.output!r} ({service_count} {noun}).")
    return 0
