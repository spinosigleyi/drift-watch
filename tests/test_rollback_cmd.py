"""Tests for drift_watch/commands/rollback_cmd.py."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from drift_watch.commands.rollback_cmd import (
    _extract_service,
    add_parser,
    run_rollback,
)
from drift_watch.snapshot import SnapshotError


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_snapshot(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "service": "api",
        "snapshot_file": "snap.json",
        "target": "out.json",
        "dry_run": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# add_parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_parser(sub)
    return p


def test_add_parser_registers_rollback_subcommand():
    p = _build_parser()
    ns = p.parse_args(["rollback", "svc", "snap.json"])
    assert ns.service == "svc"
    assert ns.snapshot_file == "snap.json"


def test_add_parser_default_dry_run_is_false():
    p = _build_parser()
    ns = p.parse_args(["rollback", "svc", "snap.json"])
    assert ns.dry_run is False


def test_add_parser_sets_func_to_run_rollback():
    p = _build_parser()
    ns = p.parse_args(["rollback", "svc", "snap.json"])
    assert ns.func is run_rollback


# ---------------------------------------------------------------------------
# _extract_service
# ---------------------------------------------------------------------------

def test_extract_service_returns_config(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"api": {"replicas": 3}})
    assert _extract_service(str(snap), "api") == {"replicas": 3}


def test_extract_service_missing_service_returns_none(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"other": {}})
    assert _extract_service(str(snap), "api") is None


def test_extract_service_bad_snapshot_returns_none():
    assert _extract_service("/nonexistent/snap.json", "api") is None


# ---------------------------------------------------------------------------
# run_rollback
# ---------------------------------------------------------------------------

def test_run_rollback_returns_zero_on_success(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"api": {"replicas": 2}})
    target = tmp_path / "out.json"
    args = _args(snapshot_file=str(snap), target=str(target))
    assert run_rollback(args) == 0


def test_run_rollback_writes_target_file(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"api": {"replicas": 2}})
    target = tmp_path / "out.json"
    args = _args(snapshot_file=str(snap), target=str(target))
    run_rollback(args)
    data = json.loads(target.read_text())
    assert data["api"]["replicas"] == 2


def test_run_rollback_returns_1_for_missing_service(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"other": {}})
    target = tmp_path / "out.json"
    args = _args(snapshot_file=str(snap), target=str(target))
    assert run_rollback(args) == 1


def test_run_rollback_dry_run_does_not_write(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"api": {"replicas": 2}})
    target = tmp_path / "out.json"
    args = _args(snapshot_file=str(snap), target=str(target), dry_run=True)
    run_rollback(args)
    assert not target.exists()


def test_run_rollback_dry_run_returns_zero(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"api": {"replicas": 2}})
    target = tmp_path / "out.json"
    args = _args(snapshot_file=str(snap), target=str(target), dry_run=True)
    assert run_rollback(args) == 0


def test_run_rollback_returns_1_on_save_error(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"api": {"replicas": 2}})
    args = _args(snapshot_file=str(snap), target="/root/no_permission/out.json")
    with patch("drift_watch.commands.rollback_cmd.save_snapshot", side_effect=SnapshotError("boom")):
        assert run_rollback(args) == 1
