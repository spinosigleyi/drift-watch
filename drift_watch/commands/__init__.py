"""Command registry for drift-watch sub-commands."""
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
)

ALL_COMMANDS = [
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
]


def register_all(subparsers) -> None:
    for cmd in ALL_COMMANDS:
        cmd.add_parser(subparsers)
