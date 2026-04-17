"""Tests for commands/__init__.py registration."""
from __future__ import annotations

import argparse

import pytest

from drift_watch.commands import _COMMANDS, register_all


def test_all_commands_have_add_parser():
    for cmd in _COMMANDS:
        assert callable(getattr(cmd, "add_parser", None)), (
            f"{cmd.__name__} missing add_parser"
        )


def test_all_commands_register_without_error():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    register_all(sub)  # should not raise


def test_diff_subcommand_is_registered():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    register_all(sub)
    args = root.parse_args(["diff", "declared.yaml", "live.yaml"])
    assert args.cmd == "diff"


def test_snapshot_subcommand_is_registered():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    register_all(sub)
    args = root.parse_args(["snapshot", "live.yaml"])
    assert args.cmd == "snapshot"


def test_export_subcommand_is_registered():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    register_all(sub)
    args = root.parse_args(["export", "declared.yaml", "live.yaml"])
    assert args.cmd == "export"


def test_search_subcommand_is_registered():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    register_all(sub)
    args = root.parse_args(["search", "api-*"])
    assert args.cmd == "search"


def test_command_count():
    assert len(_COMMANDS) == 14
