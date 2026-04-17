"""Register all sub-commands with the top-level argument parser."""
from __future__ import annotations

import argparse

from drift_watch.commands import (
    alert_cmd,
    annotate_cmd,
    baseline_cmd,
    compare_cmd,
    diff_cmd,
    export_cmd,
    history_cmd,
    ignore_cmd,
    prune_cmd,
    snapshot_cmd,
    summary_cmd,
    tag_cmd,
    watch_cmd,
)

_COMMANDS = [
    alert_cmd,
    annotate_cmd,
    baseline_cmd,
    compare_cmd,
    diff_cmd,
    export_cmd,
    history_cmd,
    ignore_cmd,
    prune_cmd,
    snapshot_cmd,
    summary_cmd,
    tag_cmd,
    watch_cmd,
]


def register_all(subparsers: argparse._SubParsersAction) -> None:
    """Call add_parser on every known command module."""
    for cmd in _COMMANDS:
        cmd.add_parser(subparsers)
