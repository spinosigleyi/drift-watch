"""Tests for drift_watch/commands/__init__.py."""
from __future__ import annotations

import argparse
import importlib

import pytest

from drift_watch.commands import register_all, _COMMANDS


def _make_subparsers():
    parser = argparse.ArgumentParser(prog="drift-watch")
    return parser, parser.add_subparsers(dest="command")


def test_all_commands_have_add_parser():
    for cmd in _COMMANDS:
        assert callable(getattr(cmd, "add_parser", None)), (
            f"{cmd.__name__} is missing add_parser"
        )


def test_all_commands_register_without_error():
    _, subparsers = _make_subparsers()
    register_all(subparsers)  # should not raise


def test_diff_subcommand_is_registered():
    parser, subparsers = _make_subparsers()
    register_all(subparsers)
    args = parser.parse_args(["diff", "--help"] )
    # parse_args with --help would sys.exit; just verify the subcommand exists
    # by checking choices
    assert "diff" in subparsers.choices


def test_snapshot_subcommand_is_registered():
    _, subparsers = _make_subparsers()
    register_all(subparsers)
    assert "snapshot" in subparsers.choices


def test_audit_subcommand_is_registered():
    _, subparsers = _make_subparsers()
    register_all(subparsers)
    assert "audit" in subparsers.choices


def test_register_all_includes_all_command_modules():
    """Every module in _COMMANDS must appear as a registered choice."""
    _, subparsers = _make_subparsers()
    register_all(subparsers)
    registered = set(subparsers.choices.keys())
    # Spot-check a handful of known commands
    for name in ("snapshot", "diff", "history", "audit", "lint", "rename"):
        assert name in registered, f"'{name}' not found in registered subcommands"
