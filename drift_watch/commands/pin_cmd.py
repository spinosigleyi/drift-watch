"""pin_cmd – pin a service's current config values as the expected baseline.

Writing a 'pinned' block into the snapshot file lets downstream commands
treate pinned values as authoritative, suppressing drift alerts for those
fields until the pin is explicitly removed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from drift_watch.snapshot import load_snapshot, save_snapshot, SnapshotError


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "pin",
        help="Pin a service's live config values so drift is suppressed for those fields.",
    )
    p.add_argument("service", help="Name of the service to pin.")
    p.add_argument(
        "--fields",
        nargs="*",
        metavar="FIELD",
        default=None,
        help="Specific fields to pin (default: all fields in the snapshot).",
    )
    p.add_argument(
        "--snapshot-dir",
        default="snapshots",
        metavar="DIR",
        help="Directory containing snapshot files (default: snapshots).",
    )
    p.add_argument(
        "--unpin",
        action="store_true",
        default=False,
        help="Remove pins for the specified service/fields instead of adding them.",
    )
    p.set_defaults(func=run_pin)


def _latest_snapshot(snapshot_dir: Path) -> Path | None:
    """Return the most recently modified snapshot JSON file, or None."""
    files = sorted(snapshot_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None


def run_pin(args: argparse.Namespace) -> int:
    snapshot_dir = Path(args.snapshot_dir)
    snapshot_path = _latest_snapshot(snapshot_dir)

    if snapshot_path is None:
        print(f"[pin] No snapshots found in '{snapshot_dir}'.")
        return 1

    try:
        data: dict[str, Any] = load_snapshot(snapshot_path)
    except SnapshotError as exc:
        print(f"[pin] Failed to load snapshot: {exc}")
        return 1

    services: dict[str, Any] = data.get("services", {})
    if args.service not in services:
        print(f"[pin] Service '{args.service}' not found in snapshot '{snapshot_path.name}'.")
        return 1

    service_data: dict[str, Any] = services[args.service]
    fields: list[str] = args.fields if args.fields is not None else list(service_data.keys())

    pins: dict[str, Any] = data.setdefault("pins", {})
    service_pins: dict[str, Any] = pins.setdefault(args.service, {})

    if args.unpin:
        removed = [f for f in fields if f in service_pins]
        for field in removed:
            del service_pins[field]
        if not service_pins:
            del pins[args.service]
        print(f"[pin] Unpinned {len(removed)} field(s) for '{args.service}'.")
    else:
        pinned = 0
        for field in fields:
            if field in service_data:
                service_pins[field] = service_data[field]
                pinned += 1
        print(f"[pin] Pinned {pinned} field(s) for '{args.service}' in '{snapshot_path.name}'.")

    try:
        save_snapshot(snapshot_path, data)
    except SnapshotError as exc:
        print(f"[pin] Failed to save snapshot: {exc}")
        return 1

    return 0
