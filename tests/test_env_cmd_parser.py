"""Parser-level tests for the env subcommand."""
from __future__ import annotations

import argparse

import pytest

from drift_watch.commands.env_cmd import add_parser, run_env


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="drift-watch")
    sub = parser.add_subparsers(dest="command")
    add_parser(sub)
    return parser


def test_add_parser_registers_env_subcommand() -> None:
    parser = _build_parser()
    ns = parser.parse_args(["env", "declared.yaml"])
    assert ns.command == "env"


def test_add_parser_sets_func_to_run_env() -> None:
    parser = _build_parser()
    ns = parser.parse_args(["env", "declared.yaml"])
    assert ns.func is run_env


def test_add_parser_default_prefix_empty() -> None:
    parser = _build_parser()
    ns = parser.parse_args(["env", "declared.yaml"])
    assert ns.prefix == ""


def test_add_parser_prefix_flag() -> None:
    parser = _build_parser()
    ns = parser.parse_args(["env", "declared.yaml", "--prefix", "MY_APP_"])
    assert ns.prefix == "MY_APP_"


def test_add_parser_exit_on_drift_flag() -> None:
    parser = _build_parser()
    ns = parser.parse_args(["env", "declared.yaml", "--exit-on-drift"])
    assert ns.exit_on_drift is True


def test_add_parser_declared_positional_stored() -> None:
    parser = _build_parser()
    ns = parser.parse_args(["env", "/path/to/config.yaml"])
    assert ns.declared == "/path/to/config.yaml"
