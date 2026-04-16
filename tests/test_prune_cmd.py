"""Tests for drift_watch/commands/prune_cmd.py."""
from __future__ import annotations

import json
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from drift_watch.commands.prune_cmd import add_parser, run_prune, _snapshot_timestamp


def _args(snapshot_dir: str, older_than: int = 30, dry_run: bool = False):
    ns = types.SimpleNamespace(
        snapshot_dir=snapshot_dir,
        older_than=older_than,
        dry_run=dry_run,
    )
    return ns


def _write_snapshot(directory: Path, filename: str, days_old: int) -> Path:
    ts = datetime.now(tz=timezone.utc) - timedelta(days=days_old)
    data = {"timestamp": ts.isoformat(), "services": {}}
    p = directory / filename
    p.write_text(json.dumps(data))
    return p


def test_add_parser_registers_prune_subcommand():
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    args = parser.parse_args(["prune"])
    assert hasattr(args, "func")
    assert args.func is run_prune


def test_missing_dir_returns_zero(tmp_path):
    result = run_prune(_args(str(tmp_path / "nonexistent")))
    assert result == 0


def test_removes_old_snapshots(tmp_path):
    _write_snapshot(tmp_path, "old.json", days_old=40)
    result = run_prune(_args(str(tmp_path), older_than=30))
    assert result == 0
    assert not (tmp_path / "old.json").exists()


def test_keeps_recent_snapshots(tmp_path):
    _write_snapshot(tmp_path, "recent.json", days_old=5)
    run_prune(_args(str(tmp_path), older_than=30))
    assert (tmp_path / "recent.json").exists()


def test_dry_run_does_not_delete(tmp_path):
    _write_snapshot(tmp_path, "old.json", days_old=40)
    run_prune(_args(str(tmp_path), older_than=30, dry_run=True))
    assert (tmp_path / "old.json").exists()


def test_snapshot_timestamp_returns_none_for_bad_file(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    assert _snapshot_timestamp(bad) is None


def test_snapshot_timestamp_returns_none_when_key_missing(tmp_path):
    p = tmp_path / "no_ts.json"
    p.write_text(json.dumps({"services": {}}))
    assert _snapshot_timestamp(p) is None


def test_mixed_ages_only_removes_old(tmp_path):
    _write_snapshot(tmp_path, "old.json", days_old=60)
    _write_snapshot(tmp_path, "new.json", days_old=2)
    run_prune(_args(str(tmp_path), older_than=30))
    assert not (tmp_path / "old.json").exists()
    assert (tmp_path / "new.json").exists()
