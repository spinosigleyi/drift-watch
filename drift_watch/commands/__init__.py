"""Register all sub-commands with the top-level argument parser."""
from __future__ import annotations

from argparse import _SubParsersAction  # noqa: PLC2701

from drift_watch.commands import (
    snapshot_cmd,
    diff_cmd,
    history_cmd,
    baseline_cmd,
    alert_cmd,
    export_cmd,
    watch_cmd,
    ignore_cmd,
    prune_cmd,
    tag_cmd,
    annotate_cmd,
    summary_cmd,
    compare_cmd,
    search_cmd,
    stats_cmd,
    lint_cmd,
    validate_cmd,
    rename_cmd,
    audit_cmd,
)

_COMMANDS = [
    snapshot_cmd,
    diff_cmd,
    history_cmd,
    baseline_cmd,
    alert_cmd,
    export_cmd,
    watch_cmd,
    ignore_cmd,
    prune_cmd,
    tag_cmd,
    annotate_cmd,
    summary_cmd,
    compare_cmd,
    search_cmd,
    stats_cmd,
    lint_cmd,
    validate_cmd,
    rename_cmd,
    audit_cmd,
]


def register_all(subparsers: _SubParsersAction) -> None:
    """Call ``add_parser`` for every known sub-command module."""
    for cmd in _COMMANDS:
        cmd.add_parser(subparsers)
