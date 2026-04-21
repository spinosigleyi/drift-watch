"""Parser-level tests for the schema subcommand."""
from __future__ import annotations

import argparse

from drift_watch.commands.schema_cmd import add_parser, run_schema


def _build_parser() -> tuple[argparse.ArgumentParser, argparse.Action]:
    parser = argparse.ArgumentParser(prog="drift-watch")
    subparsers = parser.add_subparsers(dest="command")
    add_parser(subparsers)
    return parser, subparsers


def test_add_parser_registers_schema_subcommand():
    parser, subparsers = _build_parser()
    choices = list(subparsers.choices.keys())
    assert "schema" in choices


def test_add_parser_sets_func_to_run_schema():
    parser, _ = _build_parser()
    args = parser.parse_args(["schema", "live.yaml", "schema.json"])
    assert args.func is run_schema


def test_add_parser_default_strict_is_false():
    parser, _ = _build_parser()
    args = parser.parse_args(["schema", "live.yaml", "schema.json"])
    assert args.strict is False


def test_add_parser_strict_flag():
    parser, _ = _build_parser()
    args = parser.parse_args(["schema", "live.yaml", "schema.json", "--strict"])
    assert args.strict is True


def test_add_parser_positional_live():
    parser, _ = _build_parser()
    args = parser.parse_args(["schema", "my_live.yaml", "my_schema.json"])
    assert args.live == "my_live.yaml"


def test_add_parser_positional_schema():
    parser, _ = _build_parser()
    args = parser.parse_args(["schema", "live.yaml", "my_schema.json"])
    assert args.schema == "my_schema.json"
