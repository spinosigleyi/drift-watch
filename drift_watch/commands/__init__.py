"""Register all sub-commands with an argparse subparsers action."""
from __future__ import annotations

import argparse

from drift_watch.commands import (
    alert_cmd,
    annotate_cmd,
    audit_cmd,
    baseline_cmd,
    compare_cmd,
    diff_cmd,
    export_cmd,
    history_cmd,
    ignore_cmd,
    lint_cmd,
    prune_cmd,
    rename_cmd,
    resolve_cmd,
    rollback_cmd,
    search_cmd,
    snapshot_cmd,
    stats_cmd,
    summary_cmd,
    tag_cmd,
    validate_cmd,
    watch_cmd,
)

_COMMANDS = [
    alert_cmd,
    annotate_cmd,
    audit_cmd,
    baseline_cmd,
    compare_cmd,
    diff_cmd,
    export_cmd,
    history_cmd,
    ignore_cmd,
    lint_cmd,
    prune_cmd,
    rename_cmd,
    resolve_cmd,
    rollback_cmd,
    search_cmd,
    snapshot_cmd,
    stats_cmd,
    summary_cmd,
    tag_cmd,
    validate_cmd,
    watch_cmd,
]


def register_all(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Call add_parser() for every known sub-command module."""
    for cmd in _COMMANDS:
        cmd.add_parser(subparsers)
