"""Register all subcommands with the top-level argument parser."""
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
    policy_cmd,
    prune_cmd,
    rename_cmd,
    resolve_cmd,
    rollback_cmd,
    schema_cmd,
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
    policy_cmd,
    prune_cmd,
    rename_cmd,
    resolve_cmd,
    rollback_cmd,
    schema_cmd,
    search_cmd,
    snapshot_cmd,
    stats_cmd,
    summary_cmd,
    tag_cmd,
    validate_cmd,
    watch_cmd,
]


def register_all(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Call add_parser() on every known command module."""
    for cmd in _COMMANDS:
        cmd.add_parser(subparsers)
