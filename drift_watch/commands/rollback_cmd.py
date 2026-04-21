"""rollback_cmd – restore a service's config from a snapshot."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from drift_watch.snapshot import SnapshotError, load_snapshot, save_snapshot


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "rollback",
        help="Restore a service's declared config from a previous snapshot.",
    )
    p.add_argument("service", help="Name of the service to roll back.")
    p.add_argument("snapshot_file", help="Path to the snapshot JSON file to restore from.")
    p.add_argument(
        "--target",
        default="rollback_output.json",
        help="Destination file to write the restored config (default: rollback_output.json).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print the restored config without writing to disk.",
    )
    p.set_defaults(func=run_rollback)


def _extract_service(snapshot_path: str, service: str) -> dict[str, Any] | None:
    """Return the config dict for *service* from *snapshot_path*, or None."""
    try:
        services = load_snapshot(snapshot_path)
    except SnapshotError:
        return None
    return services.get(service)


def run_rollback(args: argparse.Namespace) -> int:
    config = _extract_service(args.snapshot_file, args.service)

    if config is None:
        print(
            f"[rollback] ERROR: service '{args.service}' not found in '{args.snapshot_file}'.",
            file=sys.stderr,
        )
        return 1

    payload = {args.service: config}

    if args.dry_run:
        print(f"[rollback] Dry-run – restored config for '{args.service}':")
        print(json.dumps(payload, indent=2))
        return 0

    try:
        save_snapshot(payload, args.target)
    except SnapshotError as exc:
        print(f"[rollback] ERROR: could not write target file: {exc}", file=sys.stderr)
        return 1

    print(f"[rollback] Restored '{args.service}' from '{args.snapshot_file}' → '{args.target}'.")
    return 0
