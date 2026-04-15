"""Tests for drift_watch/commands/history_cmd.py."""
from __future__ import annotations

import argparse
import json
import os
import pytest

from drift_watch.commands.history_cmd import add_parser, run_history, _collect_snapshots


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _args(snapshot_dir: str, as_json: bool = False) -> argparse.Namespace:
    return argparse.Namespace(snapshot_dir=snapshot_dir, as_json=as_json)


def _write_snapshot(directory, filename: str, data: dict) -> None:
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


# ---------------------------------------------------------------------------
# _collect_snapshots
# ---------------------------------------------------------------------------

def test_collect_returns_empty_for_missing_dir(tmp_path):
    result = _collect_snapshots(str(tmp_path / "nonexistent"))
    assert result == []


def test_collect_finds_json_files(tmp_path):
    _write_snapshot(tmp_path, "snap1.json", {"svc-a": {}, "svc-b": {}})
    _write_snapshot(tmp_path, "snap2.json", {"svc-c": {}})
    result = _collect_snapshots(str(tmp_path))
    assert len(result) == 2


def test_collect_counts_services(tmp_path):
    _write_snapshot(tmp_path, "snap.json", {"a": {}, "b": {}, "c": {}})
    result = _collect_snapshots(str(tmp_path))
    assert result[0]["services"] == 3


def test_collect_handles_corrupt_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json at all", encoding="utf-8")
    result = _collect_snapshots(str(tmp_path))
    assert len(result) == 1
    assert result[0]["services"] is None


# ---------------------------------------------------------------------------
# run_history
# ---------------------------------------------------------------------------

def test_run_history_no_snapshots_returns_zero(tmp_path, capsys):
    rc = run_history(_args(str(tmp_path / "empty")))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No snapshots found" in out


def test_run_history_text_output(tmp_path, capsys):
    _write_snapshot(tmp_path, "2024-01-01.json", {"web": {}, "db": {}})
    rc = run_history(_args(str(tmp_path)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "2024-01-01.json" in out
    assert "Total: 1 snapshot(s)" in out


def test_run_history_json_output(tmp_path, capsys):
    _write_snapshot(tmp_path, "snap.json", {"svc": {}})
    rc = run_history(_args(str(tmp_path), as_json=True))
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert isinstance(parsed, list)
    assert parsed[0]["services"] == 1


def test_add_parser_registers_history(tmp_path):
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_parser(sub)
    ns = root.parse_args(["history", "--snapshot-dir", str(tmp_path)])
    assert ns.snapshot_dir == str(tmp_path)
    assert hasattr(ns, "func")
