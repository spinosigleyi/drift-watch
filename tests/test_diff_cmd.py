"""Tests for drift_watch.commands.diff_cmd."""
from __future__ import annotations

import json
import argparse
import pytest

from drift_watch.commands.diff_cmd import run_diff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "snapshot": "snap.json",
        "live": "live.yaml",
        "json_output": False,
        "exit_code": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


SNAPSHOT_DATA = {
    "web": {"replicas": 3, "image": "nginx:1.25"},
    "worker": {"replicas": 2, "image": "myapp:latest"},
}

LIVE_MATCHING = {
    "web": {"replicas": 3, "image": "nginx:1.25"},
    "worker": {"replicas": 2, "image": "myapp:latest"},
}

LIVE_DRIFTED = {
    "web": {"replicas": 5, "image": "nginx:1.25"},  # replicas changed
    "worker": {"replicas": 2, "image": "myapp:latest"},
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_diff_no_drift_exits_zero(tmp_path, capsys):
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps(SNAPSHOT_DATA))
    live = tmp_path / "live.json"
    live.write_text(json.dumps(LIVE_MATCHING))

    code = run_diff(_args(snapshot=str(snap), live=str(live), exit_code=True))
    assert code == 0


def test_diff_drift_exits_one_with_flag(tmp_path, capsys):
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps(SNAPSHOT_DATA))
    live = tmp_path / "live.json"
    live.write_text(json.dumps(LIVE_DRIFTED))

    code = run_diff(_args(snapshot=str(snap), live=str(live), exit_code=True))
    assert code == 1


def test_diff_drift_exits_zero_without_flag(tmp_path):
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps(SNAPSHOT_DATA))
    live = tmp_path / "live.json"
    live.write_text(json.dumps(LIVE_DRIFTED))

    code = run_diff(_args(snapshot=str(snap), live=str(live), exit_code=False))
    assert code == 0


def test_diff_bad_snapshot_returns_1(tmp_path):
    live = tmp_path / "live.json"
    live.write_text(json.dumps(LIVE_MATCHING))

    code = run_diff(_args(snapshot="nonexistent.json", live=str(live)))
    assert code == 1


def test_diff_bad_live_returns_1(tmp_path):
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps(SNAPSHOT_DATA))

    code = run_diff(_args(snapshot=str(snap), live="nonexistent.yaml"))
    assert code == 1


def test_diff_json_output(tmp_path, capsys):
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps(SNAPSHOT_DATA))
    live = tmp_path / "live.json"
    live.write_text(json.dumps(LIVE_MATCHING))

    run_diff(_args(snapshot=str(snap), live=str(live), json_output=True))
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "services" in parsed
