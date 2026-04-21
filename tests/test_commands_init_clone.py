"""Verify that clone_cmd is wired into the commands registry."""
from __future__ import annotations

import argparse

from drift_watch.commands import register_all
from drift_watch.commands.clone_cmd import run_clone


def _make_subparsers():
    parser = argparse.ArgumentParser(prog="drift-watch")
    return parser, parser.add_subparsers(dest="command")


def test_clone_subcommand_is_registered():
    parser, subparsers = _make_subparsers()
    register_all(subparsers)
    ns = parser.parse_args(["clone", "src.json", "dst.json", "svc-a"])
    assert ns.command == "clone"


def test_clone_func_is_run_clone():
    parser, subparsers = _make_subparsers()
    register_all(subparsers)
    ns = parser.parse_args(["clone", "src.json", "dst.json", "svc-a"])
    assert ns.func is run_clone


def test_clone_rename_flag_via_register_all():
    parser, subparsers = _make_subparsers()
    register_all(subparsers)
    ns = parser.parse_args(["clone", "src.json", "dst.json", "svc-a", "--rename", "svc-copy"])
    assert ns.rename == "svc-copy"


def test_clone_overwrite_flag_via_register_all():
    parser, subparsers = _make_subparsers()
    register_all(subparsers)
    ns = parser.parse_args(["clone", "src.json", "dst.json", "svc-a", "--overwrite"])
    assert ns.overwrite is True
