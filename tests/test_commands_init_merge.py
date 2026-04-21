"""Verify that the merge subcommand is wired into commands/__init__.py."""
from __future__ import annotations

import argparse

from drift_watch.commands import register_all
from drift_watch.commands.merge_cmd import run_merge


def _make_subparsers():
    parser = argparse.ArgumentParser(prog="drift-watch")
    return parser, parser.add_subparsers(dest="command")


def test_merge_subcommand_is_registered():
    parser, subparsers = _make_subparsers()
    register_all(subparsers)
    ns = parser.parse_args(["merge", "a.json", "b.json"])
    assert ns.command == "merge"


def test_merge_func_is_run_merge():
    parser, subparsers = _make_subparsers()
    register_all(subparsers)
    ns = parser.parse_args(["merge", "a.json", "b.json"])
    assert ns.func is run_merge


def test_merge_default_output_via_register_all():
    parser, subparsers = _make_subparsers()
    register_all(subparsers)
    ns = parser.parse_args(["merge", "a.json", "b.json"])
    assert ns.output == "merged_snapshot.json"


def test_merge_dry_run_flag_via_register_all():
    parser, subparsers = _make_subparsers()
    register_all(subparsers)
    ns = parser.parse_args(["merge", "a.json", "b.json", "--dry-run"])
    assert ns.dry_run is True
