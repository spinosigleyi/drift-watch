"""Tests for drift_watch/commands/__init__.py."""
from __future__ import annotations

import argparse
import importlib
import pkgutil

import pytest

import drift_watch.commands as commands_pkg
from drift_watch.commands import _COMMANDS, register_all


def _make_subparsers() -> argparse._SubParsersAction:  # type: ignore[type-arg]
    p = argparse.ArgumentParser()
    return p.add_subparsers()


def test_all_commands_have_add_parser():
    for cmd in _COMMANDS:
        assert callable(getattr(cmd, "add_parser", None)), (
            f"{cmd.__name__} is missing add_parser()"
        )


def test_all_commands_register_without_error():
    sub = _make_subparsers()
    register_all(sub)  # should not raise


def test_diff_subcommand_is_registered():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    register_all(sub)
    ns = p.parse_args(["diff", "declared.yaml", "snap.json"])
    assert ns.cmd == "diff"


def test_snapshot_subcommand_is_registered():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    register_all(sub)
    ns = p.parse_args(["snapshot", "declared.yaml"])
    assert ns.cmd == "snapshot"


def test_rollback_subcommand_is_registered():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    register_all(sub)
    ns = p.parse_args(["rollback", "api", "snap.json"])
    assert ns.cmd == "rollback"


def test_command_count_matches_commands_list():
    """Every module in the commands package (except __init__) should appear in _COMMANDS."""
    module_names = {
        name
        for _, name, _ in pkgutil.iter_modules(commands_pkg.__path__)
        if name != "__init__"
    }
    registered_names = {cmd.__name__.split(".")[-1] for cmd in _COMMANDS}
    assert module_names == registered_names
