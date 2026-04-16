"""Tests for drift_watch/commands/annotate_cmd.py."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from drift_watch.commands.annotate_cmd import (
    _read_snapshot,
    _write_snapshot,
    run_annotate,
    add_parser,
)
from drift_watch.snapshot import SnapshotError


def _args(snapshot: str, note: str, author: str = "") -> Namespace:
    return Namespace(snapshot=snapshot, note=note, author=author)


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def test_add_parser_registers_annotate_subcommand():
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    args = parser.parse_args(["annotate", "snap.json", "--note", "hi"])
    assert args.func is run_annotate


def test_run_annotate_adds_note(tmp_path):
    snap = tmp_path / "snap.json"
    _write(snap, {"services": {}})
    rc = run_annotate(_args(str(snap), "first note"))
    assert rc == 0
    data = json.loads(snap.read_text())
    assert data["annotations"][0]["note"] == "first note"


def test_run_annotate_includes_author(tmp_path):
    snap = tmp_path / "snap.json"
    _write(snap, {})
    run_annotate(_args(str(snap), "my note", author="alice"))
    data = json.loads(snap.read_text())
    assert data["annotations"][0]["author"] == "alice"


def test_run_annotate_omits_author_when_empty(tmp_path):
    snap = tmp_path / "snap.json"
    _write(snap, {})
    run_annotate(_args(str(snap), "no author"))
    data = json.loads(snap.read_text())
    assert "author" not in data["annotations"][0]


def test_run_annotate_appends_multiple_notes(tmp_path):
    snap = tmp_path / "snap.json"
    _write(snap, {})
    run_annotate(_args(str(snap), "note 1"))
    run_annotate(_args(str(snap), "note 2"))
    data = json.loads(snap.read_text())
    assert len(data["annotations"]) == 2


def test_run_annotate_missing_file_returns_1(tmp_path):
    rc = run_annotate(_args(str(tmp_path / "missing.json"), "x"))
    assert rc == 1


def test_run_annotate_bad_json_returns_1(tmp_path):
    snap = tmp_path / "bad.json"
    snap.write_text("not json")
    rc = run_annotate(_args(str(snap), "x"))
    assert rc == 1


def test_read_snapshot_raises_on_missing(tmp_path):
    with pytest.raises(SnapshotError):
        _read_snapshot(tmp_path / "nope.json")


def test_read_snapshot_raises_on_bad_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{bad")
    with pytest.raises(SnapshotError):
        _read_snapshot(p)
