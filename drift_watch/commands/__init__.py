"""Subcommand registry for drift-watch."""
from drift_watch.commands import (
    snapshot_cmd,
    diff_cmd,
    history_cmd,
    baseline_cmd,
    alert_cmd,
)

ALL_COMMANDS = [snapshot_cmd, diff_cmd, history_cmd, baseline_cmd, alert_cmd]
