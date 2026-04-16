"""Tests for drift_watch/commands/baseline_cmd.py."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from drift_watch.commands.baseline_cmd import add_parser, run_baseline
from drift_watch.loader import ConfigLoadError
from drift_watch.snapshot import SnapshotError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _args(live: str = "live.yaml", output: str = ".drift_watch/baseline.json", note: str = "") -> argparse.Namespace:
    return argparse.Namespace(live=live, output=output, note=note)


_FAKE_SERVICES = {
    "api": {"image": "api:1.0", "replicas": 2},
    "worker": {"image": "worker:1.0", "replicas": 1},
}


# ---------------------------------------------------------------------------
# add_parser
# ---------------------------------------------------------------------------

def test_add_parser_registers_baseline_subcommand():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    add_parser(subs)
    ns = root.parse_args(["baseline", "live.yaml"])
    assert ns.live == "live.yaml"


def test_add_parser_defaults():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    add_parser(subs)
    ns = root.parse_args(["baseline", "live.yaml"])
    assert ns.output == ".drift_watch/baseline.json"
    assert ns.note == ""


# ---------------------------------------------------------------------------
# run_baseline — happy path
# ---------------------------------------------------------------------------

def test_run_baseline_returns_zero_on_success():
    with patch("drift_watch.commands.baseline_cmd.load_live_config", return_value=_FAKE_SERVICES), \
         patch("drift_watch.commands.baseline_cmd.save_snapshot") as mock_save:
        code = run_baseline(_args())
    assert code == 0
    mock_save.assert_called_once()


def test_run_baseline_payload_contains_metadata():
    captured: dict = {}

    def _capture(payload, path):
        captured.update(payload)

    with patch("drift_watch.commands.baseline_cmd.load_live_config", return_value=_FAKE_SERVICES), \
         patch("drift_watch.commands.baseline_cmd.save_snapshot", side_effect=_capture):
        run_baseline(_args(note="release v2"))

    assert "__baseline__" in captured
    meta = captured["__baseline__"]
    assert meta["note"] == "release v2"
    assert "captured_at" in meta
    assert "source" in meta


def test_run_baseline_prints_service_count(capsys):
    with patch("drift_watch.commands.baseline_cmd.load_live_config", return_value=_FAKE_SERVICES), \
         patch("drift_watch.commands.baseline_cmd.save_snapshot"):
        run_baseline(_args())

    out = capsys.readouterr().out
    assert "2 services" in out


# ---------------------------------------------------------------------------
# run_baseline — error paths
# ---------------------------------------------------------------------------

def test_run_baseline_returns_nonzero_on_config_load_error(capsys):
    with patch(
        "drift_watch.commands.baseline_cmd.load_live_config",
        side_effect=ConfigLoadError("file not found"),
    ):
        code = run_baseline(_args(live="missing.yaml"))

    assert code != 0
    err = capsys.readouterr().err
    assert "file not found" in err


def test_run_baseline_returns_nonzero_on_snapshot_error(capsys):
    with patch("drift_watch.commands.baseline_cmd.load_live_config", return_value=_FAKE_SERVICES), \
         patch(
             "drift_watch.commands.baseline_cmd.save_snapshot",
             side_effect=SnapshotError("disk full"),
         ):
        code = run_baseline(_args())

    assert code != 0
    err = capsys.readouterr().err
    assert "disk full" in err
