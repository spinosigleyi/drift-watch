"""Parser-level tests for the policy subcommand."""
from __future__ import annotations

import argparse

import pytest

from drift_watch.commands.policy_cmd import add_parser, run_policy


def _build_parser() -> tuple[argparse.ArgumentParser, argparse.Action]:
    parser = argparse.ArgumentParser(prog="drift-watch")
    sub = parser.add_subparsers(dest="command")
    add_parser(sub)
    return parser, sub


def test_add_parser_registers_policy_subcommand():
    parser, _ = _build_parser()
    ns = parser.parse_args(["policy", "policy.yaml", "snap.json"])
    assert ns.command == "policy"


def test_add_parser_sets_func_to_run_policy():
    parser, _ = _build_parser()
    ns = parser.parse_args(["policy", "policy.yaml", "snap.json"])
    assert ns.func is run_policy


def test_add_parser_default_strict_is_false():
    parser, _ = _build_parser()
    ns = parser.parse_args(["policy", "policy.yaml", "snap.json"])
    assert ns.strict is False


def test_add_parser_strict_flag():
    parser, _ = _build_parser()
    ns = parser.parse_args(["policy", "policy.yaml", "snap.json", "--strict"])
    assert ns.strict is True


def test_add_parser_positional_policy_file():
    parser, _ = _build_parser()
    ns = parser.parse_args(["policy", "my_policy.yaml", "snap.json"])
    assert ns.policy_file == "my_policy.yaml"


def test_add_parser_positional_snapshot():
    parser, _ = _build_parser()
    ns = parser.parse_args(["policy", "p.yaml", "my_snap.json"])
    assert ns.snapshot == "my_snap.json"


def test_add_parser_missing_positionals_raises():
    parser, _ = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["policy"])
