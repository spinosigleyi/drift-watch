"""Verify that the trend subcommand is wired into the commands registry."""
from __future__ import annotations

import argparse

from drift_watch.commands import register_all
from drift_watch.commands.trend_cmd import run_trend


def _make_subparsers():
    root = argparse.ArgumentParser(prog="drift-watch")
    sub = root.add_subparsers(dest="command")
    register_all(sub)
    return root, sub


def test_trend_subcommand_is_registered():
    _, sub = _make_subparsers()
    assert "trend" in sub.choices


def test_trend_func_is_run_trend():
    root, _ = _make_subparsers()
    args = root.parse_args(["trend"])
    assert args.func is run_trend


def test_trend_default_snapshot_dir_via_register_all():
    root, _ = _make_subparsers()
    args = root.parse_args(["trend"])
    assert args.snapshot_dir == "snapshots"


def test_trend_json_flag_via_register_all():
    root, _ = _make_subparsers()
    args = root.parse_args(["trend", "--json"])
    assert args.json is True


def test_trend_last_flag_via_register_all():
    root, _ = _make_subparsers()
    args = root.parse_args(["trend", "--last", "7"])
    assert args.last == 7
