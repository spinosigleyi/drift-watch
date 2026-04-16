"""Tests for drift_watch/commands/summary_cmd.py"""
from __future__ import annotations

import argparse
import json
import types
from pathlib import Path

import pytest

from drift_watch.commands.summary_cmd import add_parser, _count_drift, run_summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _args(snapshot_dir: str, top: int = 5) -> argparse.Namespace:
    return argparse.Namespace(snapshot_dir=snapshot_dir, top=top)


def _write_snapshot(directory: Path, name: str, services: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(json.dumps({"services": services}))


# ---------------------------------------------------------------------------
# _count_drift
# ---------------------------------------------------------------------------

def test_count_drift_empty():
    assert _count_drift([]) == {}


def test_count_drift_no_drift():
    snaps = [{"services": {"svc-a": {"status": "ok"}}}]
    assert _count_drift(snaps) == {}


def test_count_drift_single_drifted():
    snaps = [{"services": {"svc-a": {"status": "drifted"}}}]
    assert _count_drift(snaps) == {"svc-a": 1}


def test_count_drift_missing_status():
    snaps = [{"services": {"svc-b": {"status": "missing"}}}]
    assert _count_drift(snaps) == {"svc-b": 1}


def test_count_drift_accumulates_across_snapshots():
    snaps = [
        {"services": {"svc-a": {"status": "drifted"}}},
        {"services": {"svc-a": {"status": "drifted"}, "svc-b": {"status": "ok"}}},
    ]
    counts = _count_drift(snaps)
    assert counts["svc-a"] == 2
    assert "svc-b" not in counts


# ---------------------------------------------------------------------------
# run_summary
# ---------------------------------------------------------------------------

def test_run_summary_no_snapshots(tmp_path, capsys):
    rc = run_summary(_args(str(tmp_path / "empty")))
    assert rc == 0
    assert "No snapshots found" in capsys.readouterr().out


def test_run_summary_no_drift(tmp_path, capsys):
    _write_snapshot(tmp_path, "snap1.json", {"svc-a": {"status": "ok"}})
    rc = run_summary(_args(str(tmp_path)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No drift detected" in out


def test_run_summary_shows_counts(tmp_path, capsys):
    _write_snapshot(tmp_path, "snap1.json", {"svc-a": {"status": "drifted"}})
    _write_snapshot(tmp_path, "snap2.json", {"svc-a": {"status": "drifted"}, "svc-b": {"status": "missing"}})
    rc = run_summary(_args(str(tmp_path)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "svc-a" in out
    assert "2" in out


def test_run_summary_top_limits_output(tmp_path, capsys):
    services = {f"svc-{i}": {"status": "drifted"} for i in range(10)}
    _write_snapshot(tmp_path, "snap1.json", services)
    run_summary(_args(str(tmp_path), top=3))
    out = capsys.readouterr().out
    assert "Top 3" in out


def test_add_parser_registers_summary_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    args = parser.parse_args(["summary"])
    assert args.func is run_summary
