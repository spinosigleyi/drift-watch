"""watch_cmd — periodically poll for drift and emit alerts."""
from __future__ import annotations

import argparse
import time
from typing import Optional

from drift_watch.loader import load_declared_config, load_live_config, ConfigLoadError
from drift_watch.detector import detect_drift
from drift_watch.alerting import build_alert_payload, dispatch_webhook
from drift_watch.reporter import format_text_report


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *watch* sub-command."""
    p = subparsers.add_parser(
        "watch",
        help="Continuously poll for drift at a fixed interval.",
    )
    p.add_argument("declared", help="Path to declared (IaC) config file.")
    p.add_argument("live", help="Path to live config file.")
    p.add_argument(
        "--interval",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 60).",
    )
    p.add_argument(
        "--webhook",
        default=None,
        metavar="URL",
        help="Webhook URL to POST drift alerts to.",
    )
    p.add_argument(
        "--once",
        action="store_true",
        help="Run a single check then exit (useful for testing).",
    )
    p.set_defaults(func=run_watch)


def _run_once(
    declared_path: str,
    live_path: str,
    webhook: Optional[str],
) -> bool:
    """Execute one drift-check cycle.  Returns True when drift is detected."""
    try:
        declared = load_declared_config(declared_path)
        live = load_live_config(live_path)
    except ConfigLoadError as exc:
        print(f"[watch] load error: {exc}")
        return False

    reports = detect_drift(declared, live)
    print(format_text_report(reports))

    drifted = any(r.status.value != "ok" for r in reports)
    if drifted and webhook:
        payload = build_alert_payload(reports)
        ok = dispatch_webhook(webhook, payload)
        if not ok:
            print(f"[watch] WARNING: failed to deliver alert to {webhook}")

    return drifted


def run_watch(args: argparse.Namespace) -> int:
    """Entry point for the *watch* sub-command."""
    print(
        f"[watch] starting — interval={args.interval}s  once={args.once}"
    )
    if args.once:
        _run_once(args.declared, args.live, args.webhook)
        return 0

    try:
        while True:
            _run_once(args.declared, args.live, args.webhook)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[watch] stopped.")
    return 0
