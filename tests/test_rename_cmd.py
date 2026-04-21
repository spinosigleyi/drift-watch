"""Tests for drift_watch/commands/rename_cmd.py."""
from __future__ import annotations

import json
from argparse import ArgumentParser, Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest

from drift_watch.commands.rename_cmd import (
    _rename_in_snapshot,
    add_parser,
    run_rename,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _args(tmp_path: Path, old_name="svc-a", new_name="svc-b", dry_run=False) -> Namespace:
    return SimpleNamespace(
        old_name=old_name,
        new_name=new_name,
        snapshot_dir=str(tmp_path),
        dry_run=dry_run,
    )


def _write_snapshot(directory: Path, name: str, services: dict) -> Path:
    p = directory / name
    p.write_text(json.dumps({"services": services}), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# add_parser
# ---------------------------------------------------------------------------

def _build_parser():
    root = ArgumentParser()
    sub = root.add_subparsers()
    add_parser(sub)
    return root


def test_add_parser_registers_rename_subcommand():
    root = _build_parser()
    ns = root.parse_args(["rename", "old", "new"])
    assert ns.old_name == "old"
    assert ns.new_name == "new"


def test_add_parser_default_snapshot_dir():
    root = _build_parser()
    ns = root.parse_args(["rename", "a", "b"])
    assert ns.snapshot_dir == "snapshots"


def test_add_parser_dry_run_flag():
    root = _build_parser()
    ns = root.parse_args(["rename", "a", "b", "--dry-run"])
    assert ns.dry_run is True


def test_add_parser_sets_func():
    root = _build_parser()
    ns = root.parse_args(["rename", "a", "b"])
    assert ns.func is run_rename


# ---------------------------------------------------------------------------
# _rename_in_snapshot
# ---------------------------------------------------------------------------

def test_rename_in_snapshot_renames_key(tmp_path):
    snap = _write_snapshot(tmp_path, "s.json", {"svc-a": {"env": "prod"}})
    changed = _rename_in_snapshot(snap, "svc-a", "svc-b")
    assert changed is True
    data = json.loads(snap.read_text())
    assert "svc-b" in data["services"]
    assert "svc-a" not in data["services"]


def test_rename_in_snapshot_returns_false_when_key_missing(tmp_path):
    snap = _write_snapshot(tmp_path, "s.json", {"other": {}})
    assert _rename_in_snapshot(snap, "svc-a", "svc-b") is False


def test_rename_in_snapshot_returns_false_on_bad_json(tmp_path):
    snap = tmp_path / "bad.json"
    snap.write_text("not json", encoding="utf-8")
    assert _rename_in_snapshot(snap, "svc-a", "svc-b") is False


# ---------------------------------------------------------------------------
# run_rename
# ---------------------------------------------------------------------------

def test_run_rename_returns_zero_on_success(tmp_path):
    _write_snapshot(tmp_path, "snap1.json", {"svc-a": {"k": "v"}})
    assert run_rename(_args(tmp_path)) == 0


def test_run_rename_updates_multiple_snapshots(tmp_path):
    _write_snapshot(tmp_path, "snap1.json", {"svc-a": {"k": "v"}})
    _write_snapshot(tmp_path, "snap2.json", {"svc-a": {"k": "v2"}})
    run_rename(_args(tmp_path))
    for fname in ("snap1.json", "snap2.json"):
        data = json.loads((tmp_path / fname).read_text())
        assert "svc-b" in data["services"]


def test_run_rename_missing_dir_returns_zero(tmp_path, capsys):
    args = _args(tmp_path / "nonexistent")
    rc = run_rename(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "not found" in out


def test_run_rename_no_snapshots_returns_zero(tmp_path, capsys):
    rc = run_rename(_args(tmp_path))
    assert rc == 0
    assert "no snapshot files found" in capsys.readouterr().out


def test_run_rename_service_not_found_message(tmp_path, capsys):
    _write_snapshot(tmp_path, "snap.json", {"other-svc": {}})
    run_rename(_args(tmp_path))
    assert "not found in any snapshot" in capsys.readouterr().out


def test_run_rename_dry_run_does_not_modify(tmp_path):
    snap = _write_snapshot(tmp_path, "snap.json", {"svc-a": {"k": "v"}})
    original = snap.read_text()
    run_rename(_args(tmp_path, dry_run=True))
    assert snap.read_text() == original


def test_run_rename_dry_run_prints_would_update(tmp_path, capsys):
    _write_snapshot(tmp_path, "snap.json", {"svc-a": {"k": "v"}})
    run_rename(_args(tmp_path, dry_run=True))
    assert "dry-run" in capsys.readouterr().out
