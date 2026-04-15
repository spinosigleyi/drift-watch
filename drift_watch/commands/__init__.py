"""Sub-command modules for drift-watch CLI."""
from drift_watch.commands import snapshot_cmd, diff_cmd

ALL_COMMANDS = [snapshot_cmd, diff_cmd]

__all__ = ["ALL_COMMANDS", "snapshot_cmd", "diff_cmd"]
