"""Integration tests: fmt subcommand is registered via commands/__init__.py."""
from __future__ import annotations

import argparse

from drift_watch.commands import register_all
from drift_watch.commands.fmt_cmd import run_fmt


def _make_subparsers() -> argparse._SubParsersAction:  # type: ignore[type-arg]
    p = argparse.ArgumentParser(prog="drift-watch")
    return p.add_subparsers(dest="command")


def test_fmt_subcommand_is_registered():
    sub = _make_subparsers()
    register_all(sub)
    p = sub._name_parser_map
    assert "fmt" in p


def test_fmt_func_is_run_fmt():
    p = argparse.ArgumentParser(prog="drift-watch")
    sub = p.add_subparsers(dest="command")
    register_all(sub)
    ns = p.parse_args(["fmt"])
    assert ns.func is run_fmt


def test_fmt_default_snapshot_dir_via_register_all():
    p = argparse.ArgumentParser(prog="drift-watch")
    sub = p.add_subparsers(dest="command")
    register_all(sub)
    ns = p.parse_args(["fmt"])
    assert ns.snapshot_dir == "snapshots"


def test_fmt_check_flag_via_register_all():
    p = argparse.ArgumentParser(prog="drift-watch")
    sub = p.add_subparsers(dest="command")
    register_all(sub)
    ns = p.parse_args(["fmt", "--check"])
    assert ns.check is True


def test_fmt_indent_flag_via_register_all():
    p = argparse.ArgumentParser(prog="drift-watch")
    sub = p.add_subparsers(dest="command")
    register_all(sub)
    ns = p.parse_args(["fmt", "--indent", "4"])
    assert ns.indent == 4
