"""verify_cmd: cross-check a snapshot against live config and report discrepancies.

Usage:
    drift-watch verify --snapshot <file> --live <file> [--strict] [--json]

Exits 0 if every service in the snapshot matches live config, 1 otherwise.
"""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from typing import Any

from drift_watch.loader import ConfigLoadError, load_live_config
from drift_watch.snapshot import SnapshotError, load_snapshot
from drift_watch.detector import detect_drift
from drift_watch.models import DriftStatus


def add_parser(subparsers: Any) -> None:  # pragma: no cover
    """Register the *verify* sub-command on *subparsers*."""
    p: ArgumentParser = subparsers.add_parser(
        "verify",
        help="cross-check a snapshot against live configuration",
    )
    p.add_argument(
        "--snapshot",
        default="snapshot.json",
        metavar="FILE",
        help="snapshot file to verify against (default: snapshot.json)",
    )
    p.add_argument(
        "--live",
        required=True,
        metavar="FILE",
        help="YAML/JSON file containing the current live configuration",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="exit 1 even when only warnings are present",
    )
    p.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        default=False,
        help="emit results as JSON instead of plain text",
    )
    p.set_defaults(func=run_verify)


def _verify_services(
    snapshot_services: dict[str, Any],
    live_config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compare each service in *snapshot_services* against *live_config*.

    Returns a list of result dicts, one per service, with keys:
        service, status, drifted_fields
    """
    results: list[dict[str, Any]] = []
    for service_name, declared in snapshot_services.items():
        if not isinstance(declared, dict):
            results.append(
                {"service": service_name, "status": "error",
                 "drifted_fields": [], "detail": "snapshot entry is not a mapping"}
            )
            continue

        live = live_config.get(service_name)
        report = detect_drift(service_name, declared, live)

        drifted = [
            {"field": f.field_name, "declared": f.declared_value, "live": f.live_value}
            for f in report.fields
            if f.status != DriftStatus.OK
        ]
        results.append(
            {
                "service": service_name,
                "status": report.status.value,
                "drifted_fields": drifted,
            }
        )
    return results


def run_verify(args: Namespace) -> int:
    """Entry point for the *verify* sub-command.

    Returns an integer exit code (0 = clean, 1 = drift or error).
    """
    # --- load snapshot ---------------------------------------------------
    try:
        snapshot = load_snapshot(args.snapshot)
    except SnapshotError as exc:
        print(f"[verify] error loading snapshot: {exc}", file=sys.stderr)
        return 1

    snapshot_services: dict[str, Any] = snapshot.get("services", {})
    if not snapshot_services:
        print("[verify] snapshot contains no services — nothing to verify.")
        return 0

    # --- load live config ------------------------------------------------
    try:
        live_config = load_live_config(args.live)
    except ConfigLoadError as exc:
        print(f"[verify] error loading live config: {exc}", file=sys.stderr)
        return 1

    # --- compare ---------------------------------------------------------
    results = _verify_services(snapshot_services, live_config)

    has_drift = any(r["status"] != DriftStatus.OK.value for r in results)

    if args.json_output:
        print(json.dumps({"results": results, "drift_detected": has_drift}, indent=2))
    else:
        for r in results:
            marker = "OK" if r["status"] == DriftStatus.OK.value else "DRIFT"
            print(f"  [{marker}] {r['service']} — {r['status']}")
            for field in r.get("drifted_fields", []):
                print(
                    f"         {field['field']}: "
                    f"declared={field['declared']!r}  live={field['live']!r}"
                )
        total = len(results)
        drifted_count = sum(1 for r in results if r["status"] != DriftStatus.OK.value)
        print(f"\nverified {total} service(s) — {drifted_count} drifted.")

    return 1 if has_drift else 0
