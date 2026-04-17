"""Register all sub-commands with an argparse subparsers action."""
from __future__ import annotations

from drift_watch.commands import (
    snapshot_cmd,
    diff_cmd,
    export_cmd,
    history_cmd,
    baseline_cmd,
    alert_cmd,
    watch_cmd,
    ignore_cmd,
    prune_cmd,
    tag_cmd,
    annotate_cmd,
    summary_cmd,
    compare_cmd,
    search_cmd,
    stats_cmd,
)

_COMMANDS = [
    snapshot_cmd,
    diff_cmd,
    export_cmd,
    history_cmd,
    baseline_cmd,
    alert_cmd,
    watch_cmd,
    ignore_cmd,
    prune_cmd,
    tag_cmd,
    annotate_cmd,
    summary_cmd,
    compare_cmd,
    search_cmd,
    stats_cmd,
]


def register_all(subparsers) -> None:
    """Call add_parser() for every known sub-command module."""
    for cmd in _COMMANDS:
        cmd.add_parser(subparsers)
