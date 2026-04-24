"""Tests for drift_watch/commands/score_cmd.py."""
from __future__ import annotations

import argparse
import json
import types
from pathlib import Path

import pytest

from drift_watch.commands.score_cmd import (
    _aggregate,
    _compute_score,
    add_parser,
    run_score,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _args(
    snapshot_dir: str = ".drift_snapshots",
    json_output: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(snapshot_dir=snapshot_dir, json_output=json_output)


def _write_snapshot(directory: Path, filename: str, services: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    data = {"services": services}
    (directory / filename).write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# _aggregate
# ---------------------------------------------------------------------------

def test_aggregate_missing_dir_returns_zeros(tmp_path):
    total, drifted = _aggregate(tmp_path / "nonexistent")
    assert total == 0
    assert drifted == 0


def test_aggregate_empty_dir_returns_zeros(tmp_path):
    d = tmp_path / "snaps"
    d.mkdir()
    total, drifted = _aggregate(d)
    assert total == 0
    assert drifted == 0


def test_aggregate_counts_ok_services(tmp_path):
    d = tmp_path / "snaps"
    _write_snapshot(d, "a.json", {"svc1": {"status": "ok"}, "svc2": {"status": "ok"}})
    total, drifted = _aggregate(d)
    assert total == 2
    assert drifted == 0


def test_aggregate_counts_drifted_services(tmp_path):
    d = tmp_path / "snaps"
    _write_snapshot(
        d,
        "a.json",
        {"svc1": {"status": "ok"}, "svc2": {"status": "drifted"}},
    )
    total, drifted = _aggregate(d)
    assert total == 2
    assert drifted == 1


def test_aggregate_across_multiple_snapshots(tmp_path):
    d = tmp_path / "snaps"
    _write_snapshot(d, "a.json", {"svc1": {"status": "drifted"}})
    _write_snapshot(d, "b.json", {"svc2": {"status": "ok"}, "svc3": {"status": "drifted"}})
    total, drifted = _aggregate(d)
    assert total == 3
    assert drifted == 2


def test_aggregate_skips_malformed_json(tmp_path):
    d = tmp_path / "snaps"
    d.mkdir()
    (d / "bad.json").write_text("not json{{")
    _write_snapshot(d, "good.json", {"svc1": {"status": "ok"}})
    total, drifted = _aggregate(d)
    assert total == 1


# ---------------------------------------------------------------------------
# _compute_score
# ---------------------------------------------------------------------------

def test_compute_score_all_ok():
    assert _compute_score(10, 0) == 100.0


def test_compute_score_all_drifted():
    assert _compute_score(4, 4) == 0.0


def test_compute_score_partial():
    assert _compute_score(10, 5) == 50.0


def test_compute_score_no_services():
    assert _compute_score(0, 0) == 100.0


# ---------------------------------------------------------------------------
# run_score
# ---------------------------------------------------------------------------

def test_run_score_returns_zero(tmp_path, capsys):
    d = tmp_path / "snaps"
    _write_snapshot(d, "a.json", {"svc1": {"status": "ok"}})
    rc = run_score(_args(snapshot_dir=str(d)))
    assert rc == 0


def test_run_score_text_output(tmp_path, capsys):
    d = tmp_path / "snaps"
    _write_snapshot(d, "a.json", {"svc1": {"status": "ok"}, "svc2": {"status": "drifted"}})
    run_score(_args(snapshot_dir=str(d)))
    out = capsys.readouterr().out
    assert "50.00" in out
    assert "Drifted          : 1" in out


def test_run_score_json_output(tmp_path, capsys):
    d = tmp_path / "snaps"
    _write_snapshot(d, "a.json", {"svc1": {"status": "ok"}})
    run_score(_args(snapshot_dir=str(d), json_output=True))
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["score"] == 100.0
    assert payload["total_services"] == 1
    assert payload["drifted_services"] == 0


# ---------------------------------------------------------------------------
# add_parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_parser(sub)
    return root


def test_add_parser_registers_score_subcommand():
    root = _build_parser()
    ns = root.parse_args(["score"])
    assert hasattr(ns, "func")


def test_add_parser_sets_func_to_run_score():
    root = _build_parser()
    ns = root.parse_args(["score"])
    assert ns.func is run_score


def test_add_parser_default_snapshot_dir():
    root = _build_parser()
    ns = root.parse_args(["score"])
    assert ns.snapshot_dir == ".drift_snapshots"


def test_add_parser_json_flag():
    root = _build_parser()
    ns = root.parse_args(["score", "--json"])
    assert ns.json_output is True
