"""alert_cmd — send drift alerts to a webhook endpoint."""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from typing import Any

from drift_watch.loader import ConfigLoadError, load_declared_config, load_live_config
from drift_watch.detector import detect_drift
from drift_watch.models import DriftStatus


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "alert",
        help="Detect drift and POST a summary to a webhook URL.",
    )
    p.add_argument("declared", help="Path to declared config file (YAML/JSON).")
    p.add_argument("live", help="Path to live config file (YAML/JSON).")
    p.add_argument("--webhook", required=True, help="Webhook URL to POST alert payload.")
    p.add_argument(
        "--only-drifted",
        action="store_true",
        default=False,
        help="Only send alert when drift is detected.",
    )
    p.set_defaults(func=run_alert)


def _build_payload(reports: list[Any]) -> dict[str, Any]:
    drifted = [
        r.service_name
        for r in reports
        if r.status in (DriftStatus.DRIFTED, DriftStatus.MISSING)
    ]
    return {
        "drift_detected": len(drifted) > 0,
        "drifted_services": drifted,
        "total_services": len(reports),
        "drifted_count": len(drifted),
    }


def _post_payload(url: str, payload: dict[str, Any]) -> bool:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except urllib.error.URLError:
        return False


def run_alert(args: argparse.Namespace) -> int:
    try:
        declared = load_declared_config(args.declared)
        live = load_live_config(args.live)
    except ConfigLoadError as exc:
        print(f"[alert] load error: {exc}")
        return 1

    reports = detect_drift(declared, live)
    payload = _build_payload(reports)

    if args.only_drifted and not payload["drift_detected"]:
        print("[alert] no drift detected — skipping webhook.")
        return 0

    success = _post_payload(args.webhook, payload)
    if not success:
        print(f"[alert] failed to reach webhook: {args.webhook}")
        return 1

    print(f"[alert] payload sent ({payload['drifted_count']} drifted service(s)).")
    return 0
