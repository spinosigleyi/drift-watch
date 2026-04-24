"""Integration tests – score subcommand registration via commands/__init__.py."""
from __future__ import annotations

import argparse

from drift_watch.commands import register_all
from drift_watch.commands.score_cmd import run_score


def _make_subparsers() -> argparse._SubParsersAction:  # noqa: SLF001
    root = argparse.ArgumentParser(prog="drift-watch")
    return root.add_subparsers(dest="command"), root


def test_score_subcommand_is_registered():
    sub, root = _make_subparsers()
    register_all(sub)
    ns = root.parse_args(["score"])
    assert ns.command == "score"


def test_score_func_is_run_score():
    sub, root = _make_subparsers()
    register_all(sub)
    ns = root.parse_args(["score"])
    assert ns.func is run_score


def test_score_default_snapshot_dir_via_register_all():
    sub, root = _make_subparsers()
    register_all(sub)
    ns = root.parse_args(["score"])
    assert ns.snapshot_dir == ".drift_snapshots"


def test_score_json_flag_via_register_all():
    sub, root = _make_subparsers()
    register_all(sub)
    ns = root.parse_args(["score", "--json"])
    assert ns.json_output is True
