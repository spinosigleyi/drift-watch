"""env_cmd: compare declared config against live environment variables."""
from __future__ import annotations

import os
import argparse
from typing import Any

from drift_watch.loader import load_declared_config, ConfigLoadError
from drift_watch.detector import detect_drift
from drift_watch.reporter import format_text_report


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "env",
        help="Compare declared config fields against live environment variables.",
    )
    p.add_argument("declared", help="Path to declared config file (YAML or JSON).")
    p.add_argument(
        "--prefix",
        default="",
        help="Only consider env vars that start with this prefix.",
    )
    p.add_argument(
        "--exit-on-drift",
        action="store_true",
        default=False,
        help="Exit with code 1 when drift is detected.",
    )
    p.set_defaults(func=run_env)


def _env_snapshot(prefix: str) -> dict[str, Any]:
    """Return a flat mapping of env vars (optionally filtered by prefix)."""
    env: dict[str, Any] = {}
    for key, value in os.environ.items():
        if prefix and not key.startswith(prefix):
            continue
        env[key] = value
    return env


def run_env(args: argparse.Namespace) -> int:
    try:
        declared = load_declared_config(args.declared)
    except ConfigLoadError as exc:
        print(f"[env] error loading declared config: {exc}")
        return 1

    prefix: str = args.prefix
    live_env = _env_snapshot(prefix)

    # Treat every top-level service in the declared config as a service name;
    # the live state is drawn from env vars whose names match the declared keys.
    reports = []
    for service_name, declared_fields in declared.items():
        live_fields: dict[str, Any] = {
            k: live_env.get(k) for k in declared_fields
        }
        report = detect_drift(service_name, declared_fields, live_fields)
        reports.append(report)

    print(format_text_report(reports))

    if args.exit_on_drift and any(r.status.value == "drifted" for r in reports):
        return 1
    return 0
