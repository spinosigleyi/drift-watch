"""Tests for drift_watch.commands.snapshot_cmd."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

from drift_watch.commands.snapshot_cmd import run_snapshot
from drift_watch.loader import ConfigLoadError
from drift_watch.snapshot import SnapshotError


SAMPLE_LIVE = {
    "api": {"replicas": "2", "image": "api:latest"},
    "db": {"replicas": "1", "image": "postgres:15"},
}


def _args(live: str, output: str) -> Namespace:
    return Namespace(live=live, output=output)


# ---------------------------------------------------------------------------
# success path
# ---------------------------------------------------------------------------

def test_run_snapshot_creates_file(tmp_path):
    live_file = tmp_path / "live.yaml"
    # Write a minimal YAML live config.
    live_file.write_text("api:\n  replicas: '2'\n  image: api:latest\n")
    output = tmp_path / "snap.json"

    code = run_snapshot(_args(str(live_file), str(output)))

    assert code == 0
    assert output.exists()
    payload = json.loads(output.read_text())
    assert "api" in payload["services"]


def test_run_snapshot_prints_service_count(tmp_path, capsys):
    live_file = tmp_path / "live.yaml"
    live_file.write_text("api:\n  replicas: '2'\n")
    output = tmp_path / "snap.json"

    run_snapshot(_args(str(live_file), str(output)))

    captured = capsys.readouterr()
    assert "1 service" in captured.out


# ---------------------------------------------------------------------------
# error paths
# ---------------------------------------------------------------------------

def test_run_snapshot_returns_1_on_load_error(tmp_path, capsys):
    with patch(
        "drift_watch.commands.snapshot_cmd.load_live_config",
        side_effect=ConfigLoadError("file not found"),
    ):
        code = run_snapshot(_args("missing.yaml", str(tmp_path / "snap.json")))

    assert code == 1
    assert "error loading live config" in capsys.readouterr().err


def test_run_snapshot_returns_1_on_save_error(tmp_path, capsys):
    with patch(
        "drift_watch.commands.snapshot_cmd.load_live_config",
        return_value=SAMPLE_LIVE,
    ), patch(
        "drift_watch.commands.snapshot_cmd.save_snapshot",
        side_effect=SnapshotError("disk full"),
    ):
        code = run_snapshot(_args("live.yaml", "/bad/path/snap.json"))

    assert code == 1
    assert "disk full" in capsys.readouterr().err


def test_run_snapshot_plural_noun(tmp_path, capsys):
    with patch(
        "drift_watch.commands.snapshot_cmd.load_live_config",
        return_value=SAMPLE_LIVE,
    ), patch("drift_watch.commands.snapshot_cmd.save_snapshot"):
        run_snapshot(_args("live.yaml", str(tmp_path / "snap.json")))

    assert "2 services" in capsys.readouterr().out
