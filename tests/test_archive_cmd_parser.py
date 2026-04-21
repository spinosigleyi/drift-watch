"""Parser-level tests for archive_cmd.add_parser."""
from __future__ import annotations

import argparse

import pytest

from drift_watch.commands.archive_cmd import (
    DEFAULT_ARCHIVE_DIR,
    DEFAULT_SNAPSHOT_DIR,
    add_parser,
    run_archive,
)


def _build_parser() -> tuple[argparse.ArgumentParser, argparse._SubParsersAction]:  # noqa: SLF001
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_parser(subparsers)
    return parser, subparsers


def test_add_parser_registers_archive_subcommand() -> None:
    parser, _ = _build_parser()
    args = parser.parse_args(["archive"])
    assert hasattr(args, "func")


def test_add_parser_sets_func_to_run_archive() -> None:
    parser, _ = _build_parser()
    args = parser.parse_args(["archive"])
    assert args.func is run_archive


def test_add_parser_default_snapshot_dir() -> None:
    parser, _ = _build_parser()
    args = parser.parse_args(["archive"])
    assert args.snapshot_dir == DEFAULT_SNAPSHOT_DIR


def test_add_parser_default_archive_dir() -> None:
    parser, _ = _build_parser()
    args = parser.parse_args(["archive"])
    assert args.archive_dir == DEFAULT_ARCHIVE_DIR


def test_add_parser_default_older_than() -> None:
    parser, _ = _build_parser()
    args = parser.parse_args(["archive"])
    assert args.older_than == 30


def test_add_parser_default_dry_run_is_false() -> None:
    parser, _ = _build_parser()
    args = parser.parse_args(["archive"])
    assert args.dry_run is False


def test_add_parser_dry_run_flag() -> None:
    parser, _ = _build_parser()
    args = parser.parse_args(["archive", "--dry-run"])
    assert args.dry_run is True


def test_add_parser_older_than_flag() -> None:
    parser, _ = _build_parser()
    args = parser.parse_args(["archive", "--older-than", "7"])
    assert args.older_than == 7


def test_add_parser_snapshot_dir_flag() -> None:
    parser, _ = _build_parser()
    args = parser.parse_args(["archive", "--snapshot-dir", "custom/snaps"])
    assert args.snapshot_dir == "custom/snaps"


def test_add_parser_archive_dir_flag() -> None:
    parser, _ = _build_parser()
    args = parser.parse_args(["archive", "--archive-dir", "custom/archives"])
    assert args.archive_dir == "custom/archives"
