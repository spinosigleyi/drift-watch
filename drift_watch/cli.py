"""Command-line interface for drift-watch."""

import sys
import argparse
from pathlib import Path

from drift_watch.loader import load_declared_config, load_live_config, ConfigLoadError
from drift_watch.detector import detect_drift
from drift_watch.reporter import format_text_report, format_json_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="drift-watch",
        description="Detect configuration drift between deployed services and IaC state.",
    )
    parser.add_argument(
        "declared",
        metavar="DECLARED_CONFIG",
        help="Path to the declared (IaC) configuration file (YAML or JSON).",
    )
    parser.add_argument(
        "live",
        metavar="LIVE_CONFIG",
        help="Path to the live (deployed) configuration file (YAML or JSON).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if any drift or missing services are detected.",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        declared = load_declared_config(Path(args.declared))
    except ConfigLoadError as exc:
        print(f"drift-watch: error loading declared config: {exc}", file=sys.stderr)
        return 2

    try:
        live = load_live_config(Path(args.live))
    except ConfigLoadError as exc:
        print(f"drift-watch: error loading live config: {exc}", file=sys.stderr)
        return 2

    reports = detect_drift(declared, live)

    if args.output_format == "json":
        print(format_json_report(reports))
    else:
        print(format_text_report(reports))

    if args.exit_code:
        from drift_watch.models import DriftStatus
        has_drift = any(
            r.status in (DriftStatus.DRIFTED, DriftStatus.MISSING) for r in reports
        )
        return 1 if has_drift else 0

    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
