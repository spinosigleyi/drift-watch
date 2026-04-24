"""Tests for drift_watch/commands/trend_cmd.py"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from drift_watch.commands.trend_cmd import (
    _collect_trend,
    _snapshot_timestamp,
    run_trend,
)


def _write_snapshot(directory: Path, filename: str, captured_at: str, services: dict) -> Path:
    path = directory / filename
    path.write_text(json.dumps({"captured_at": captured_at, "services": services}))
    return path


def _args(**kwargs):
    defaults = {"snapshot_dir": "snapshots", "last": 10, "json": False}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# --- _snapshot_timestamp ---

def test_snapshot_timestamp_valid(tmp_path):
    f = tmp_path / "snap.json"
    f.write_text(json.dumps({"captured_at": "2024-06-01T12:00:00"}))
    ts = _snapshot_timestamp(f)
    assert ts.year == 2024
    assert ts.month == 6


def test_snapshot_timestamp_missing_key(tmp_path):
    f = tmp_path / "snap.json"
    f.write_text(json.dumps({}))
    ts = _snapshot_timestamp(f)
    assert ts == datetime.fromtimestamp(0, tz=timezone.utc)


def test_snapshot_timestamp_invalid_file(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("not json")
    ts = _snapshot_timestamp(f)
    assert ts == datetime.fromtimestamp(0, tz=timezone.utc)


# --- _collect_trend ---

def test_collect_missing_dir_returns_empty():
    result = _collect_trend("/nonexistent/dir", 10)
    assert result == []


def test_collect_returns_data_points(tmp_path):
    _write_snapshot(
        tmp_path, "a.json", "2024-01-01T00:00:00",
        {"svc-a": {"status": "ok"}, "svc-b": {"status": "drifted"}},
    )
    result = _collect_trend(str(tmp_path), 10)
    assert len(result) == 1
    assert result[0]["total"] == 2
    assert result[0]["drifted"] == 1
    assert result[0]["drift_rate"] == pytest.approx(0.5, rel=1e-3)


def test_collect_respects_last_limit(tmp_path):
    for i in range(5):
        _write_snapshot(
            tmp_path, f"snap{i}.json", f"2024-0{i+1}-01T00:00:00",
            {"svc": {"status": "ok"}},
        )
    result = _collect_trend(str(tmp_path), 3)
    assert len(result) == 3


def test_collect_no_services_gives_zero_rate(tmp_path):
    _write_snapshot(tmp_path, "empty.json", "2024-03-01T00:00:00", {})
    result = _collect_trend(str(tmp_path), 10)
    assert result[0]["drift_rate"] == 0.0
    assert result[0]["total"] == 0


def test_collect_skips_malformed_file(tmp_path):
    (tmp_path / "bad.json").write_text("not json")
    _write_snapshot(tmp_path, "good.json", "2024-05-01T00:00:00", {"s": {"status": "ok"}})
    result = _collect_trend(str(tmp_path), 10)
    assert len(result) == 1


# --- run_trend ---

def test_run_trend_no_snapshots_returns_zero(tmp_path, capsys):
    rc = run_trend(_args(snapshot_dir=str(tmp_path)))
    assert rc == 0
    assert "No snapshots found" in capsys.readouterr().out


def test_run_trend_text_output(tmp_path, capsys):
    _write_snapshot(
        tmp_path, "s.json", "2024-07-01T08:00:00",
        {"api": {"status": "drifted"}, "db": {"status": "ok"}},
    )
    rc = run_trend(_args(snapshot_dir=str(tmp_path)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "2024-07-01" in out
    assert "50.00%" in out


def test_run_trend_json_output(tmp_path, capsys):
    _write_snapshot(
        tmp_path, "s.json", "2024-08-15T10:00:00",
        {"x": {"status": "ok"}},
    )
    rc = run_trend(_args(snapshot_dir=str(tmp_path), json=True))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["total"] == 1
    assert data[0]["drifted"] == 0
