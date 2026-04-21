"""Verify that the report subcommand is registered via register_all."""
from __future__ import annotations

import argparse

from drift_watch.commands import register_all
from drift_watch.commands.report_cmd import run_report


def _make_subparsers() -> argparse._SubParsersAction:  # noqa: SLF001
    parser = argparse.ArgumentParser()
    return parser.add_subparsers(dest="command")


def test_report_subcommand_is_registered():
    sub = _make_subparsers()
    register_all(sub)
    parser = sub._parser_class()
    choices = sub.choices  # type: ignore[attr-defined]
    assert "report" in choices


def test_report_func_is_run_report():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    register_all(sub)
    ns = parser.parse_args(["report"])
    assert ns.func is run_report


def test_report_default_output_via_register_all():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    register_all(sub)
    ns = parser.parse_args(["report"])
    assert ns.output == "text"


def test_report_json_flag_via_register_all():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    register_all(sub)
    ns = parser.parse_args(["report", "--output", "json"])
    assert ns.output == "json"
