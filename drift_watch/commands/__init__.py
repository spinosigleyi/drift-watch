"""Registry of all drift-watch sub-commands."""

from drift_watch.commands import (
    snapshot_cmd,
    diff_cmd,
    history_cmd,
    baseline_cmd,
    alert_cmd,
    export_cmd,
)

ALL_COMMANDS = [
    snapshot_cmd,
    diff_cmd,
    history_cmd,
    baseline_cmd,
    alert_cmd,
    export_cmd,
]
