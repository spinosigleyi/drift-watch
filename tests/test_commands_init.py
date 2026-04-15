"""Smoke tests for the commands package registry."""
from __future__ import annotations

import argparse

from drift_watch.commands import ALL_COMMANDS


def test_all_commands_have_add_parser():
    for cmd in ALL_COMMANDS:
        assert callable(getattr(cmd, "add_parser", None)), (
            f"{cmd.__name__} must expose add_parser()"
        )


def test_all_commands_register_without_error():
    parser = argparse.ArgumentParser(prog="drift-watch")
    subparsers = parser.add_subparsers()
    for cmd in ALL_COMMANDS:
        cmd.add_parser(subparsers)  # should not raise


def test_diff_subcommand_is_registered():
    parser = argparse.ArgumentParser(prog="drift-watch")
    subparsers = parser.add_subparsers(dest="command")
    from drift_watch.commands import diff_cmd
    diff_cmd.add_parser(subparsers)

    args = parser.parse_args(["diff", "snap.json", "live.yaml"])
    assert args.command == "diff"
    assert args.snapshot == "snap.json"
    assert args.live == "live.yaml"
    assert args.json_output is False
    assert args.exit_code is False


def test_snapshot_subcommand_is_registered():
    parser = argparse.ArgumentParser(prog="drift-watch")
    subparsers = parser.add_subparsers(dest="command")
    from drift_watch.commands import snapshot_cmd
    snapshot_cmd.add_parser(subparsers)

    args = parser.parse_args(["snapshot", "declared.yaml", "out.json"])
    assert args.command == "snapshot"
