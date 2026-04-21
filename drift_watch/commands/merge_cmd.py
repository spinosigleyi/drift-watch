"""merge_cmd – merge two snapshots into a single output snapshot."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from drift_watch.snapshot import SnapshotError, load_snapshot, save_snapshot


def add_parser(subparsers: Any) -> None:  # noqa: ANN401
    p = subparsers.add_parser(
        "merge",
        help="Merge two snapshots into one, with the second taking precedence.",
    )
    p.add_argument("base", help="Path to the base snapshot file.")
    p.add_argument("override", help="Path to the snapshot whose values win on conflict.")
    p.add_argument(
        "--output",
        default="merged_snapshot.json",
        help="Destination file for the merged snapshot (default: merged_snapshot.json).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print the merged result without writing to disk.",
    )
    p.set_defaults(func=run_merge)


def _merge_snapshots(
    base: dict[str, Any], override: dict[str, Any]
) -> dict[str, Any]:
    """Return a new dict that is *base* updated with every key in *override*.

    Top-level metadata keys (``timestamp``, ``tags``, ``notes``) from *override*
    are preserved when present; ``services`` dicts are merged per-service.
    """
    merged: dict[str, Any] = dict(base)

    for meta_key in ("timestamp", "tags", "notes"):
        if meta_key in override:
            merged[meta_key] = override[meta_key]

    base_services: dict[str, Any] = dict(base.get("services", {}))
    override_services: dict[str, Any] = override.get("services", {})
    base_services.update(override_services)
    merged["services"] = base_services

    return merged


def run_merge(args: Any) -> int:  # noqa: ANN401
    try:
        base_data = load_snapshot(args.base)
    except SnapshotError as exc:
        print(f"[merge] error reading base snapshot: {exc}")
        return 1

    try:
        override_data = load_snapshot(args.override)
    except SnapshotError as exc:
        print(f"[merge] error reading override snapshot: {exc}")
        return 1

    # load_snapshot returns the services dict; we need the raw JSON for metadata.
    def _raw(path: str) -> dict[str, Any]:
        with open(path) as fh:
            return json.load(fh)

    raw_base = _raw(args.base)
    raw_override = _raw(args.override)

    merged = _merge_snapshots(raw_base, raw_override)
    service_count = len(merged.get("services", {}))

    if args.dry_run:
        print(json.dumps(merged, indent=2))
        print(f"[merge] dry-run: {service_count} service(s) in merged snapshot.")
        return 0

    try:
        save_snapshot(merged["services"], args.output, extra={
            k: v for k, v in merged.items() if k != "services"
        })
    except SnapshotError as exc:
        print(f"[merge] error writing merged snapshot: {exc}")
        return 1

    print(f"[merge] wrote {service_count} service(s) to {args.output}")
    return 0
