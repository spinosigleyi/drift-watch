"""Tests for drift_watch/commands/health_cmd.py."""
from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from drift_watch.commands.health_cmd import (
    _collect_health,
    _latest_snapshot,
    run_health,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _args(snapshot_dir: str, *, json_output: bool = False, fail_on_drift: bool = False):
    return SimpleNamespace(
        snapshot_dir=snapshot_dir,
        json_output=json_output,
        fail_on_drift=fail_on_drift,
    )


def _write_snapshot(directory: Path, filename: str, services: dict) -> Path:
    path = directory / filename
    path.write_text(json.dumps({"services": services}))
    return path


# ---------------------------------------------------------------------------
# _latest_snapshot
# ---------------------------------------------------------------------------

def test_latest_snapshot_returns_none_for_empty_dir(tmp_path):
    assert _latest_snapshot(tmp_path) is None


def test_latest_snapshot_returns_most_recent(tmp_path):
    p1 = _write_snapshot(tmp_path, "a.json", {"svc-a": {"status": "ok"}})
    time.sleep(0.02)
    _write_snapshot(tmp_path, "b.json", {"svc-b": {"status": "drifted"}})
    data = _latest_snapshot(tmp_path)
    assert "svc-b" in data["services"]


# ---------------------------------------------------------------------------
# _collect_health
# ---------------------------------------------------------------------------

def test_collect_health_empty_services():
    assert _collect_health({"services": {}}) == []


def test_collect_health_ok_service():
    data = {"services": {"api": {"status": "ok"}}}
    records = _collect_health(data)
    assert records == [{"service": "api", "status": "ok"}]


def test_collect_health_drifted_service():
    data = {"services": {"worker": {"status": "drifted"}}}
    records = _collect_health(data)
    assert records[0]["status"] == "drifted"


def test_collect_health_missing_status_defaults_to_unknown():
    data = {"services": {"db": {"version": "1.2"}}}
    records = _collect_health(data)
    assert records[0]["status"] == "unknown"


def test_collect_health_non_dict_service_defaults_to_unknown():
    data = {"services": {"cache": None}}
    records = _collect_health(data)
    assert records[0]["status"] == "unknown"


# ---------------------------------------------------------------------------
# run_health
# ---------------------------------------------------------------------------

def test_run_health_missing_dir_returns_zero(tmp_path):
    rc = run_health(_args(str(tmp_path / "nonexistent")))
    assert rc == 0


def test_run_health_no_snapshots_returns_zero(tmp_path):
    rc = run_health(_args(str(tmp_path)))
    assert rc == 0


def test_run_health_all_ok_returns_zero(tmp_path):
    _write_snapshot(tmp_path, "snap.json", {"api": {"status": "ok"}})
    rc = run_health(_args(str(tmp_path)))
    assert rc == 0


def test_run_health_drift_without_flag_returns_zero(tmp_path):
    _write_snapshot(tmp_path, "snap.json", {"api": {"status": "drifted"}})
    rc = run_health(_args(str(tmp_path), fail_on_drift=False))
    assert rc == 0


def test_run_health_drift_with_flag_returns_one(tmp_path):
    _write_snapshot(tmp_path, "snap.json", {"api": {"status": "drifted"}})
    rc = run_health(_args(str(tmp_path), fail_on_drift=True))
    assert rc == 1


def test_run_health_json_output_is_valid(tmp_path, capsys):
    _write_snapshot(tmp_path, "snap.json", {"api": {"status": "ok"}})
    run_health(_args(str(tmp_path), json_output=True))
    captured = capsys.readouterr().out
    payload = json.loads(captured)
    assert "services" in payload
    assert "drifted_count" in payload


def test_run_health_text_output_contains_service_name(tmp_path, capsys):
    _write_snapshot(tmp_path, "snap.json", {"my-service": {"status": "ok"}})
    run_health(_args(str(tmp_path)))
    assert "my-service" in capsys.readouterr().out
