"""Tests for drift_watch/commands/__init__.py command registry."""

from __future__ import annotations

import argparse

import pytest

from drift_watch.commands import ALL_COMMANDS


def test_all_commands_have_add_parser():
    for cmd in ALL_COMMANDS:
        assert hasattr(cmd, "add_parser"), f"{cmd.__name__} missing add_parser"


def test_all_commands_register_without_error():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    for cmd in ALL_COMMANDS:
        cmd.add_parser(sub)  # should not raise


def test_diff_subcommand_is_registered():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    for cmd in ALL_COMMANDS:
        cmd.add_parser(sub)
    args = root.parse_args(["diff", "snap.json", "live.yaml"])
    from drift_watch.commands.diff_cmd import run_diff
    assert args.func is run_diff


def test_snapshot_subcommand_is_registered():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    for cmd in ALL_COMMANDS:
        cmd.add_parser(sub)
    args = root.parse_args(["snapshot", "live.yaml", "snap.json"])
    from drift_watch.commands.snapshot_cmd import run_snapshot
    assert args.func is run_snapshot


def test_export_subcommand_is_registered():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    for cmd in ALL_COMMANDS:
        cmd.add_parser(sub)
    args = root.parse_args(
        ["export", "declared.yaml", "live.yaml", "--output", "out.txt"]
    )
    from drift_watch.commands.export_cmd import run_export
    assert args.func is run_export


def test_all_commands_count():
    assert len(ALL_COMMANDS) == 6
