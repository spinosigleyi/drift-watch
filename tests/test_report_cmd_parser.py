"""Parser-level tests for report_cmd to keep concerns separate."""
from __future__ import annotations

import argparse

from drift_watch.commands.report_cmd import add_parser, run_report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_parser(sub)
    return parser


def test_add_parser_registers_report_subcommand():
    parser = _build_parser()
    ns = parser.parse_args(["report"])
    assert ns.command == "report"


def test_add_parser_sets_func_to_run_report():
    parser = _build_parser()
    ns = parser.parse_args(["report"])
    assert ns.func is run_report


def test_add_parser_default_snapshot_dir():
    parser = _build_parser()
    ns = parser.parse_args(["report"])
    assert ns.snapshot_dir == "snapshots"


def test_add_parser_snapshot_dir_flag():
    parser = _build_parser()
    ns = parser.parse_args(["report", "--snapshot-dir", "my_snaps"])
    assert ns.snapshot_dir == "my_snaps"


def test_add_parser_output_json():
    parser = _build_parser()
    ns = parser.parse_args(["report", "--output", "json"])
    assert ns.output == "json"


def test_add_parser_out_file_flag():
    parser = _build_parser()
    ns = parser.parse_args(["report", "--out-file", "out.txt"])
    assert ns.out_file == "out.txt"


def test_add_parser_default_out_file_is_none():
    parser = _build_parser()
    ns = parser.parse_args(["report"])
    assert ns.out_file is None
