"""Tests for drift_watch/commands/__init__.py registry."""
from __future__ import annotations

import argparse

import pytest

from drift_watch.commands import ALL_COMMANDS, register_all


def test_all_commands_have_add_parser():
    for cmd in ALL_COMMANDS:
        assert callable(getattr(cmd, "add_parser", None)), (
            f"{cmd.__name__} missing add_parser"
        )


def test_all_commands_register_without_error():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_all(sub)  # should not raise


def test_diff_subcommand_is_registered():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    register_all(sub)
    args = parser.parse_args(["diff", "--help"] if False else ["diff"])
    assert True  # parsing didn't raise


def test_snapshot_subcommand_is_registered():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    register_all(sub)
    parser.parse_args(["snapshot"])


def test_export_subcommand_is_registered():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    register_all(sub)
    parser.parse_args(["export"])


def test_annotate_subcommand_is_registered():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    register_all(sub)
    args = parser.parse_args(["annotate", "snap.json", "--note", "hi"])
    assert args.cmd == "annotate"


def test_all_commands_count():
    assert len(ALL_COMMANDS) == 11
