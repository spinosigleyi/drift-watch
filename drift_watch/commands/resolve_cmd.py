"""resolve_cmd: mark drifted fields as resolved in a snapshot."""
from __future__ import annotations

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from drift_watch.snapshot import SnapshotError, load_snapshot, save_snapshot


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "resolve",
        help="Mark drifted fields as resolved in a snapshot file.",
    )
    p.add_argument("snapshot", help="Path to the snapshot JSON file.")
    p.add_argument(
        "--service",
        required=True,
        help="Name of the service whose drift to resolve.",
    )
    p.add_argument(
        "--fields",
        nargs="+",
        metavar="FIELD",
        default=None,
        help="Specific field names to resolve. Omit to resolve all drifted fields.",
    )
    p.add_argument(
        "--note",
        default="",
        help="Optional resolution note to attach.",
    )
    p.set_defaults(func=run_resolve)


def _resolve_service(
    services: dict[str, Any],
    service_name: str,
    fields: list[str] | None,
    note: str,
    resolved_at: str,
) -> tuple[bool, list[str]]:
    """Mutate *services* in-place; return (found, resolved_field_names)."""
    if service_name not in services:
        return False, []

    svc = services[service_name]
    drifted = svc.get("drifted_fields", [])
    if fields is not None:
        targets = [f for f in drifted if f in fields]
    else:
        targets = list(drifted)

    for field in targets:
        drifted.remove(field)

    svc["drifted_fields"] = drifted
    if not drifted:
        svc["status"] = "ok"

    resolutions = svc.setdefault("resolutions", [])
    for field in targets:
        resolutions.append({"field": field, "note": note, "resolved_at": resolved_at})

    return True, targets


def run_resolve(args: argparse.Namespace) -> int:
    snapshot_path = Path(args.snapshot)
    try:
        services = load_snapshot(snapshot_path)
    except SnapshotError as exc:
        print(f"[error] Could not load snapshot: {exc}")
        return 1

    resolved_at = datetime.now(timezone.utc).isoformat()
    found, resolved = _resolve_service(
        services, args.service, args.fields, args.note, resolved_at
    )

    if not found:
        print(f"[error] Service '{args.service}' not found in snapshot.")
        return 1

    if not resolved:
        print(f"[info] No matching drifted fields to resolve for '{args.service}'.")
        return 0

    try:
        save_snapshot(snapshot_path, services)
    except SnapshotError as exc:
        print(f"[error] Could not save snapshot: {exc}")
        return 1

    print(f"[ok] Resolved {len(resolved)} field(s) for '{args.service}': {', '.join(resolved)}")
    return 0
