"""Parser-level tests for the trend subcommand."""
from __future__ import annotations

import argparse

import pytest

from drift_watch.commands.trend_cmd import add_parser, run_trend


def _build_parser() -> tuple[argparse.ArgumentParser, argparse.Action]:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    add_parser(sub)
    return root, sub


def test_add_parser_registers_trend_subcommand():
    root, sub = _build_parser()
    choices = sub.choices
    assert "trend" in choices


def test_add_parser_sets_func_to_run_trend():
    root, _ = _build_parser()
    args = root.parse_args(["trend"])
    assert args.func is run_trend


def test_add_parser_default_snapshot_dir():
    root, _ = _build_parser()
    args = root.parse_args(["trend"])
    assert args.snapshot_dir == "snapshots"


def test_add_parser_snapshot_dir_flag():
    root, _ = _build_parser()
    args = root.parse_args(["trend", "--snapshot-dir", "/custom/path"])
    assert args.snapshot_dir == "/custom/path"


def test_add_parser_default_last_is_ten():
    root, _ = _build_parser()
    args = root.parse_args(["trend"])
    assert args.last == 10


def test_add_parser_last_flag():
    root, _ = _build_parser()
    args = root.parse_args(["trend", "--last", "5"])
    assert args.last == 5


def test_add_parser_default_json_is_false():
    root, _ = _build_parser()
    args = root.parse_args(["trend"])
    assert args.json is False


def test_add_parser_json_flag():
    root, _ = _build_parser()
    args = root.parse_args(["trend", "--json"])
    assert args.json is True
