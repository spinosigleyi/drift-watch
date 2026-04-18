"""Tests for lint_cmd.add_parser integration."""
from __future__ import annotations

import argparse

from drift_watch.commands.lint_cmd import add_parser, run_lint


def _build_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_parser(subparsers)
    return parser


def test_add_parser_registers_lint_subcommand():
    parser = _build_parser()
    subparsers_action = [
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    ][0]
    assert "lint" in subparsers_action.choices


def test_add_parser_sets_func_to_run_lint():
    parser = _build_parser()
    args = parser.parse_args(["lint", "declared.yaml"])
    assert args.func is run_lint


def test_add_parser_default_strict_is_false():
    parser = _build_parser()
    args = parser.parse_args(["lint", "declared.yaml"])
    assert args.strict is False


def test_add_parser_strict_flag():
    parser = _build_parser()
    args = parser.parse_args(["lint", "declared.yaml", "--strict"])
    assert args.strict is True


def test_add_parser_declared_positional():
    parser = _build_parser()
    args = parser.parse_args(["lint", "/path/to/config.yaml"])
    assert args.declared == "/path/to/config.yaml"
