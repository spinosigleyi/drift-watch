"""clone_cmd: copy a service's config from one snapshot to another."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from drift_watch.snapshot import SnapshotError, load_snapshot, save_snapshot


def add_parser(subparsers: Any) -> None:  # noqa: ANN401
    p = subparsers.add_parser(
        "clone",
        help="Copy a service entry from one snapshot file to another.",
    )
    p.add_argument("source", help="Path to the source snapshot JSON file.")
    p.add_argument("destination", help="Path to the destination snapshot JSON file.")
    p.add_argument("service", help="Name of the service to clone.")
    p.add_argument(
        "--rename",
        metavar="NEW_NAME",
        default=None,
        help="Store the cloned service under a different name in the destination.",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite the service in the destination if it already exists.",
    )
    p.set_defaults(func=run_clone)


def _load_raw(path: str) -> dict[str, Any]:
    """Load a snapshot file and return its raw dict."""
    p = Path(path)
    if not p.exists():
        raise SnapshotError(f"Snapshot not found: {path}")
    with p.open() as fh:
        return json.load(fh)


def run_clone(args: Any) -> int:  # noqa: ANN401
    """Execute the clone command.  Returns 0 on success, 1 on error."""
    try:
        src_data = _load_raw(args.source)
    except (SnapshotError, json.JSONDecodeError) as exc:
        print(f"[clone] ERROR reading source: {exc}")
        return 1

    services: dict[str, Any] = src_data.get("services", {})
    if args.service not in services:
        print(f"[clone] ERROR service '{args.service}' not found in source snapshot.")
        return 1

    target_name: str = args.rename if args.rename else args.service
    service_data = services[args.service]

    dest_path = Path(args.destination)
    if dest_path.exists():
        try:
            dest_data = _load_raw(args.destination)
        except (SnapshotError, json.JSONDecodeError) as exc:
            print(f"[clone] ERROR reading destination: {exc}")
            return 1
    else:
        dest_data = {"services": {}}

    dest_services: dict[str, Any] = dest_data.setdefault("services", {})

    if target_name in dest_services and not args.overwrite:
        print(
            f"[clone] ERROR service '{target_name}' already exists in destination. "
            "Use --overwrite to replace it."
        )
        return 1

    dest_services[target_name] = service_data

    try:
        save_snapshot(dest_data["services"], args.destination)
    except SnapshotError as exc:
        print(f"[clone] ERROR saving destination: {exc}")
        return 1

    action = "Overwrote" if target_name in dest_services and args.overwrite else "Cloned"
    print(f"[clone] {action} '{args.service}' -> '{target_name}' in {args.destination}")
    return 0
