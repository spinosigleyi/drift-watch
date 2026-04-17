"""Tests for drift_watch/commands/compare_cmd.py."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from drift_watch.commands.compare_cmd import add_parser, _compare_snapshots, run_compare


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_snapshot(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _args(tmp_path, a_data, b_data, as_json=False):
    a = tmp_path / "snap_a.json"
    b = tmp_path / "snap_b.json"
    _write_snapshot(a, a_data)
    _write_snapshot(b, b_data)
    ns = argparse.Namespace(snapshot_a=str(a), snapshot_b=str(b), as_json=as_json)
    return ns


SVC_A = {"image": "nginx:1.0", "replicas": "2"}
SVC_B = {"image": "nginx:1.1", "replicas": "2"}


# ---------------------------------------------------------------------------
# _compare_snapshots unit tests
# ---------------------------------------------------------------------------

def test_compare_no_diff():
    result = _compare_snapshots({"web": SVC_A}, {"web": SVC_A})
    assert result == {"added": [], "removed": [], "changed": {}}


def test_compare_added_service():
    result = _compare_snapshots({}, {"web": SVC_A})
    assert "web" in result["added"]


def test_compare_removed_service():
    result = _compare_snapshots({"web": SVC_A}, {})
    assert "web" in result["removed"]


def test_compare_changed_field():
    result = _compare_snapshots({"web": SVC_A}, {"web": SVC_B})
    assert "web" in result["changed"]
    assert result["changed"]["web"]["image"]["old"] == "nginx:1.0"
    assert result["changed"]["web"]["image"]["new"] == "nginx:1.1"


def test_compare_added_field():
    result = _compare_snapshots({"web": {"a": "1"}}, {"web": {"a": "1", "b": "2"}})
    assert "b" in result["changed"]["web"]
    assert result["changed"]["web"]["b"]["old"] is None


# ---------------------------------------------------------------------------
# run_compare integration tests
# ---------------------------------------------------------------------------

def test_run_compare_no_diff_exits_zero(tmp_path, capsys):
    ns = _args(tmp_path, {"web": SVC_A}, {"web": SVC_A})
    assert run_compare(ns) == 0
    assert "No differences" in capsys.readouterr().out


def test_run_compare_diff_exits_zero(tmp_path, capsys):
    ns = _args(tmp_path, {"web": SVC_A}, {"web": SVC_B})
    assert run_compare(ns) == 0
    out = capsys.readouterr().out
    assert "web" in out
    assert "nginx:1.0" in out


def test_run_compare_json_output(tmp_path, capsys):
    ns = _args(tmp_path, {"web": SVC_A}, {"web": SVC_B}, as_json=True)
    assert run_compare(ns) == 0
    data = json.loads(capsys.readouterr().out)
    assert "changed" in data


def test_run_compare_bad_snapshot_returns_1(tmp_path):
    ns = argparse.Namespace(
        snapshot_a=str(tmp_path / "missing_a.json"),
        snapshot_b=str(tmp_path / "missing_b.json"),
        as_json=False,
    )
    assert run_compare(ns) == 1


def test_add_parser_registers_compare_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    ns = parser.parse_args(["compare", "a.json", "b.json"])
    assert ns.snapshot_a == "a.json"
    assert ns.snapshot_b == "b.json"
