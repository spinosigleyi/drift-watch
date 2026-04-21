"""Tests for drift_watch/commands/archive_cmd.py."""
from __future__ import annotations

import json
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from drift_watch.commands.archive_cmd import (
    _collect_old_snapshots,
    _snapshot_timestamp,
    run_archive,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _args(
    tmp_path: Path,
    *,
    older_than: int = 30,
    dry_run: bool = False,
    snapshot_dir: str | None = None,
    archive_dir: str | None = None,
):
    import argparse

    ns = argparse.Namespace()
    ns.snapshot_dir = snapshot_dir or str(tmp_path / "snapshots")
    ns.archive_dir = archive_dir or str(tmp_path / "archives")
    ns.older_than = older_than
    ns.dry_run = dry_run
    return ns


def _write_snapshot(directory: Path, name: str, days_old: int) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(tz=timezone.utc) - timedelta(days=days_old)
    data = {"timestamp": ts.isoformat(), "services": {}}
    p = directory / name
    p.write_text(json.dumps(data))
    return p


# ---------------------------------------------------------------------------
# _snapshot_timestamp
# ---------------------------------------------------------------------------

def test_snapshot_timestamp_valid(tmp_path: Path) -> None:
    ts = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    p = tmp_path / "snap.json"
    p.write_text(json.dumps({"timestamp": ts.isoformat()}))
    result = _snapshot_timestamp(p)
    assert result is not None
    assert result.year == 2024


def test_snapshot_timestamp_missing_key(tmp_path: Path) -> None:
    p = tmp_path / "snap.json"
    p.write_text(json.dumps({"services": {}}))
    assert _snapshot_timestamp(p) is None


def test_snapshot_timestamp_invalid_file(tmp_path: Path) -> None:
    p = tmp_path / "snap.json"
    p.write_text("not json")
    assert _snapshot_timestamp(p) is None


# ---------------------------------------------------------------------------
# _collect_old_snapshots
# ---------------------------------------------------------------------------

def test_collect_returns_empty_for_missing_dir(tmp_path: Path) -> None:
    result = _collect_old_snapshots(tmp_path / "no_such", 30)
    assert result == []


def test_collect_finds_old_snapshots(tmp_path: Path) -> None:
    snap_dir = tmp_path / "snapshots"
    _write_snapshot(snap_dir, "old.json", days_old=60)
    _write_snapshot(snap_dir, "recent.json", days_old=5)
    result = _collect_old_snapshots(snap_dir, 30)
    assert len(result) == 1
    assert result[0].name == "old.json"


def test_collect_ignores_non_json_files(tmp_path: Path) -> None:
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    (snap_dir / "notes.txt").write_text("hello")
    result = _collect_old_snapshots(snap_dir, 30)
    assert result == []


# ---------------------------------------------------------------------------
# run_archive
# ---------------------------------------------------------------------------

def test_run_archive_no_candidates_returns_zero(tmp_path: Path, capsys) -> None:
    snap_dir = tmp_path / "snapshots"
    _write_snapshot(snap_dir, "recent.json", days_old=5)
    rc = run_archive(_args(tmp_path))
    assert rc == 0
    captured = capsys.readouterr()
    assert "No snapshots" in captured.out


def test_run_archive_dry_run_does_not_delete(tmp_path: Path, capsys) -> None:
    snap_dir = tmp_path / "snapshots"
    _write_snapshot(snap_dir, "old.json", days_old=60)
    rc = run_archive(_args(tmp_path, dry_run=True))
    assert rc == 0
    assert (snap_dir / "old.json").exists()
    captured = capsys.readouterr()
    assert "Would archive" in captured.out


def test_run_archive_creates_tar_gz(tmp_path: Path) -> None:
    snap_dir = tmp_path / "snapshots"
    _write_snapshot(snap_dir, "old.json", days_old=60)
    archive_dir = tmp_path / "archives"
    rc = run_archive(_args(tmp_path, archive_dir=str(archive_dir)))
    assert rc == 0
    archives = list(archive_dir.glob("*.tar.gz"))
    assert len(archives) == 1


def test_run_archive_removes_originals(tmp_path: Path) -> None:
    snap_dir = tmp_path / "snapshots"
    _write_snapshot(snap_dir, "old.json", days_old=60)
    run_archive(_args(tmp_path))
    assert not (snap_dir / "old.json").exists()


def test_run_archive_tar_contains_snapshot(tmp_path: Path) -> None:
    snap_dir = tmp_path / "snapshots"
    _write_snapshot(snap_dir, "old.json", days_old=60)
    archive_dir = tmp_path / "archives"
    run_archive(_args(tmp_path, archive_dir=str(archive_dir)))
    archive = next(archive_dir.glob("*.tar.gz"))
    with tarfile.open(archive, "r:gz") as tar:
        names = tar.getnames()
    assert "old.json" in names


def test_run_archive_missing_snapshot_dir_returns_zero(tmp_path: Path) -> None:
    rc = run_archive(_args(tmp_path))
    assert rc == 0
