"""Formats and outputs drift reports to various targets (stdout, JSON, etc.)."""

from __future__ import annotations

import json
import sys
from typing import List, TextIO

from drift_watch.models import DriftStatus, ServiceDriftReport


STATUS_SYMBOLS = {
    DriftStatus.OK: "✓",
    DriftStatus.DRIFTED: "✗",
    DriftStatus.MISSING: "?",
}

STATUS_COLORS = {
    DriftStatus.OK: "\033[32m",      # green
    DriftStatus.DRIFTED: "\033[31m", # red
    DriftStatus.MISSING: "\033[33m", # yellow
}

RESET = "\033[0m"


def _colorize(text: str, status: DriftStatus, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{STATUS_COLORS[status]}{text}{RESET}"


def format_text_report(
    reports: List[ServiceDriftReport],
    use_color: bool = True,
    out: TextIO = sys.stdout,
) -> None:
    """Write a human-readable drift report to *out*."""
    for report in reports:
        symbol = STATUS_SYMBOLS[report.status]
        header = f"{symbol} {report.service_name} [{report.status.value}]"
        out.write(_colorize(header, report.status, use_color) + "\n")

        if report.status == DriftStatus.MISSING:
            out.write("  Service not found in live environment.\n")
            continue

        for field in report.drifted_fields:
            line = (
                f"  - {field.key}: "
                f"expected={field.expected!r}, "
                f"actual={field.actual!r}"
            )
            out.write(line + "\n")

        if not report.drifted_fields:
            out.write("  All fields match.\n")

    total = len(reports)
    drifted = sum(1 for r in reports if r.status == DriftStatus.DRIFTED)
    missing = sum(1 for r in reports if r.status == DriftStatus.MISSING)
    summary = f"\nSummary: {total} service(s) checked, {drifted} drifted, {missing} missing.\n"
    out.write(summary)


def format_json_report(reports: List[ServiceDriftReport]) -> str:
    """Return a JSON string representation of all drift reports."""
    data = [
        {
            "service": r.service_name,
            "status": r.status.value,
            "drifted_fields": [
                {"key": f.key, "expected": f.expected, "actual": f.actual}
                for f in r.drifted_fields
            ],
        }
        for r in reports
    ]
    return json.dumps(data, indent=2)
