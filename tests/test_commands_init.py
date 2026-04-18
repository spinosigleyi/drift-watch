"""Tests for commands/__init__.py registration."""
from __future__ import annotations

import argparse
import importlib

import pytest

from drift_watch.commands import register_all, _COMMANDS


def _make_subparsers():
    parser = argparse.ArgumentParser()
    return parser, parser.add_subparsers()


def test_all_commands_have_add_parser():
    for cmd in _COMMANDS:
        assert callable(getattr(cmd, "add_parser", None)), f"{cmd} missing add_parser"


def test_all_commands_register_without_error():
    _, subparsers = _make_sub_all(subparsers)  # should not raise


def test_diff_subcommand_is_registered():
    parser, subparsers = _make_subparsers()
    register_all(subparsers)
    args = parser.parse_args(["diff", "--help"] if False else [])
    # just ensure 'diff' key exists in choices
    assert "diff" in subparsers.choices


def test_snapshot_subcommand_is_registered():
    _, subparsers = _make_subparsers()
    register_all(subparsers)
    assert "snapshot" in subparsers.choices


def test_export_subcommand_is_registered():
    _, subparsers = _make_subparsers()
    register_all(subparsers)
    assert "export" in subparsers.choices


def test_lint_subcommand_is_registered():
    _, subparsers = _make_subparsers()
    register_all(subparsers)
    assert "lint" in subparsers.choices


def test_total_command_count():
    assert len(_COMMANDS) == 16
