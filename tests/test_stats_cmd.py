"""Tests for drift_watch/commands/stats_cmd.py."""
from __future__ import annotations

import json
import pathlib
import types

import pytest

from drift_watch.commands.stats_cmd import _aggregate, add_parser, run_stats


def _args(tmp_path, as_json=False):
    ns = types.SimpleNamespace(
        snapshot_dir=str(tmp_path),
        as_json=as_json,
    )
    return ns


def _write_snapshot(directory: pathlib.Path, name: str, services: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(json.dumps({"services": services}))


# ---------------------------------------------------------------------------
# _aggregate
# ---------------------------------------------------------------------------

def test_aggregate_missing_dir_returns_zeros(tmp_path):
    result = _aggregate(str(tmp_path / "nonexistent"))
    assert result["snapshots"] == 0
    assert result["total_services"] == 0
    assert result["drifted_services"] == 0
    assert result["drift_rate"] == 0.0


def test_aggregate_counts_snapshots(tmp_path):
    for i in range(3):
        _write_snapshot(tmp_path, f"snap{i}.json", {})
    result = _aggregate(str(tmp_path))
    assert result["snapshots"] == 3


def test_aggregate_no_drift(tmp_path):
    services = {
        "svc-a": {"port": {"drifted": False}},
        "svc-b": {"port": {"drifted": False}},
    }
    _write_snapshot(tmp_path, "snap.json", services)
    result = _aggregate(str(tmp_path))
    assert result["total_services"] == 2
    assert result["drifted_services"] == 0
    assert result["drift_rate"] == 0.0


def test_aggregate_with_drift(tmp_path):
    services = {
        "svc-a": {"port": {"drifted": True}},
        "svc-b": {"port": {"drifted": False}},
    }
    _write_snapshot(tmp_path, "snap.json", services)
    result = _aggregate(str(tmp_path))
    assert result["drifted_services"] == 1
    assert result["drift_rate"] == pytest.approx(0.5)


def test_aggregate_skips_malformed_files(tmp_path):
    (tmp_path / "bad.json").write_text("{not valid json")
    _write_snapshot(tmp_path, "good.json", {"svc": {"k": {"drifted": False}}})
    result = _aggregate(str(tmp_path))
    assert result["total_services"] == 1


# ---------------------------------------------------------------------------
# run_stats
# ---------------------------------------------------------------------------

def test_run_stats_returns_zero(tmp_path):
    assert run_stats(_args(tmp_path)) == 0


def test_run_stats_text_output(tmp_path, capsys):
    _write_snapshot(tmp_path, "s.json", {"svc": {"port": {"drifted": True}}})
    run_stats(_args(tmp_path))
    out = capsys.readouterr().out
    assert "Snapshots analysed" in out
    assert "Drift rate" in out


def test_run_stats_json_output(tmp_path, capsys):
    _write_snapshot(tmp_path, "s.json", {"svc": {"port": {"drifted": False}}})
    run_stats(_args(tmp_path, as_json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "drift_rate" in data
    assert "snapshots" in data


# ---------------------------------------------------------------------------
# add_parser
# ---------------------------------------------------------------------------

def test_add_parser_registers_stats_subcommand():
    import argparse
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_parser(sub)
    args = root.parse_args(["stats", "--snapshot-dir", "/tmp"])
    assert args.snapshot_dir == "/tmp"
    assert args.func is run_stats
