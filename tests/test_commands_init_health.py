"""Verify that the health subcommand is wired into the command registry."""
from __future__ import annotations

import argparse

import pytest

from drift_watch.commands import register_all
from drift_watch.commands.health_cmd import add_parser, run_health


def _make_subparsers():
    parser = argparse.ArgumentParser(prog="drift-watch")
    return parser, parser.add_subparsers(dest="command")


def test_health_subcommand_is_registered():
    _, subparsers = _make_subparsers()
    add_parser(subparsers)
    assert "health" in subparsers.choices


def test_health_func_is_run_health():
    _, subparsers = _make_subparsers()
    add_parser(subparsers)
    ns = subparsers.choices["health"].parse_args([])
    assert ns.func is run_health


def test_health_default_snapshot_dir_via_register_all():
    parser = argparse.ArgumentParser(prog="drift-watch")
    subparsers = parser.add_subparsers(dest="command")
    register_all(subparsers)
    ns = subparsers.choices["health"].parse_args([])
    assert ns.snapshot_dir == ".drift_snapshots"


def test_health_json_flag_via_register_all():
    parser = argparse.ArgumentParser(prog="drift-watch")
    subparsers = parser.add_subparsers(dest="command")
    register_all(subparsers)
    ns = subparsers.choices["health"].parse_args(["--json"])
    assert ns.json_output is True


def test_health_fail_on_drift_flag_via_register_all():
    parser = argparse.ArgumentParser(prog="drift-watch")
    subparsers = parser.add_subparsers(dest="command")
    register_all(subparsers)
    ns = subparsers.choices["health"].parse_args(["--fail-on-drift"])
    assert ns.fail_on_drift is True
