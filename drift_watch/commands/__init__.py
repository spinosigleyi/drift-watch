"""Register all sub-commands with the top-level argument parser."""
from __future__ import annotations

import argparse
import importlib
from typing import Protocol


class _CommandModule(Protocol):
    def add_parser(self, subparsers: argparse._SubParsersAction) -> None: ...  # noqa: SLF001


_COMMAND_MODULES = [
    "drift_watch.commands.snapshot_cmd",
    "drift_watch.commands.diff_cmd",
    "drift_watch.commands.history_cmd",
    "drift_watch.commands.baseline_cmd",
    "drift_watch.commands.alert_cmd",
    "drift_watch.commands.export_cmd",
    "drift_watch.commands.watch_cmd",
    "drift_watch.commands.ignore_cmd",
    "drift_watch.commands.prune_cmd",
    "drift_watch.commands.tag_cmd",
    "drift_watch.commands.annotate_cmd",
    "drift_watch.commands.summary_cmd",
    "drift_watch.commands.compare_cmd",
    "drift_watch.commands.search_cmd",
    "drift_watch.commands.stats_cmd",
    "drift_watch.commands.lint_cmd",
    "drift_watch.commands.validate_cmd",
    "drift_watch.commands.rename_cmd",
    "drift_watch.commands.audit_cmd",
    "drift_watch.commands.resolve_cmd",
    "drift_watch.commands.rollback_cmd",
    "drift_watch.commands.schema_cmd",
    "drift_watch.commands.policy_cmd",
    "drift_watch.commands.env_cmd",
    "drift_watch.commands.report_cmd",
]


def register_all(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Import every command module and call its *add_parser* function."""
    for module_path in _COMMAND_MODULES:
        module: _CommandModule = importlib.import_module(module_path)  # type: ignore[assignment]
        module.add_parser(subparsers)
