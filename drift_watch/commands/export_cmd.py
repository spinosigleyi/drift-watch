"""export_cmd — export drift reports to a file in text or JSON format."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from drift_watch.loader import ConfigLoadError, load_declared_config, load_live_config
from drift_watch.detector import detect_drift
from drift_watch.reporter import format_text_report, format_json_report


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "export",
        help="Run drift detection and export the report to a file.",
    )
    p.add_argument("declared", help="Path to declared (IaC) config file.")
    p.add_argument("live", help="Path to live config file.")
    p.add_argument(
        "--output", "-o", required=True, help="Destination file path for the report."
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--fail-on-drift",
        action="store_true",
        default=False,
        help="Exit with code 1 if drift is detected.",
    )
    p.set_defaults(func=run_export)


def _build_report_content(reports: list, fmt: str) -> str:
    """Render *reports* to a string in the requested format.

    Args:
        reports: List of drift report objects returned by ``detect_drift``.
        fmt: Either ``"json"`` or ``"text"``.

    Returns:
        The formatted report as a string.
    """
    if fmt == "json":
        return format_json_report(reports)
    return format_text_report(reports)


def run_export(args: argparse.Namespace) -> int:
    try:
        declared = load_declared_config(args.declared)
        live = load_live_config(args.live)
    except ConfigLoadError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    reports = detect_drift(declared, live)
    content = _build_report_content(reports, args.format)

    output_path = Path(args.output)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"[error] Could not write report: {exc}", file=sys.stderr)
        return 1

    drifted = any(
        r.status.value in ("drifted", "missing") for r in reports
    )
    service_count = len(reports)
    print(f"Report written to {output_path} ({service_count} service(s) checked).")

    if args.fail_on_drift and drifted:
        return 1
    return 0
