"""Tests for drift_watch/commands/merge_cmd.py."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from drift_watch.commands.merge_cmd import _merge_snapshots, add_parser, run_merge
from drift_watch.snapshot import SnapshotError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_snapshot(path: Path, services: dict, **extra) -> None:
    payload = {"services": services, **extra}
    path.write_text(json.dumps(payload))


def _args(tmp_path: Path, **kwargs):
    base = tmp_path / "base.json"
    override = tmp_path / "override.json"
    _write_snapshot(base, {"svc-a": {"replicas": 1}})
    _write_snapshot(override, {"svc-b": {"replicas": 2}})
    defaults = dict(
        base=str(base),
        override=str(override),
        output=str(tmp_path / "merged.json"),
        dry_run=False,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Unit tests for _merge_snapshots
# ---------------------------------------------------------------------------

def test_merge_snapshots_combines_services():
    base = {"services": {"a": {"x": 1}}, "timestamp": "t1"}
    override = {"services": {"b": {"y": 2}}}
    result = _merge_snapshots(base, override)
    assert "a" in result["services"]
    assert "b" in result["services"]


def test_merge_snapshots_override_wins_on_conflict():
    base = {"services": {"a": {"replicas": 1}}}
    override = {"services": {"a": {"replicas": 5}}}
    result = _merge_snapshots(base, override)
    assert result["services"]["a"]["replicas"] == 5


def test_merge_snapshots_metadata_from_override():
    base = {"services": {}, "timestamp": "old", "tags": ["v1"]}
    override = {"services": {}, "timestamp": "new", "tags": ["v2"]}
    result = _merge_snapshots(base, override)
    assert result["timestamp"] == "new"
    assert result["tags"] == ["v2"]


def test_merge_snapshots_keeps_base_metadata_when_override_absent():
    base = {"services": {}, "notes": "keep me"}
    override = {"services": {}}
    result = _merge_snapshots(base, override)
    assert result["notes"] == "keep me"


# ---------------------------------------------------------------------------
# run_merge integration
# ---------------------------------------------------------------------------

def test_run_merge_creates_output_file(tmp_path):
    args = _args(tmp_path)
    rc = run_merge(args)
    assert rc == 0
    assert Path(args.output).exists()


def test_run_merge_output_contains_both_services(tmp_path):
    args = _args(tmp_path)
    run_merge(args)
    data = json.loads(Path(args.output).read_text())
    assert "svc-a" in data["services"]
    assert "svc-b" in data["services"]


def test_run_merge_dry_run_does_not_write(tmp_path, capsys):
    args = _args(tmp_path, dry_run=True)
    rc = run_merge(args)
    assert rc == 0
    assert not Path(args.output).exists()
    captured = capsys.readouterr()
    assert "dry-run" in captured.out


def test_run_merge_bad_base_returns_1(tmp_path):
    args = _args(tmp_path, base="/nonexistent/base.json")
    rc = run_merge(args)
    assert rc == 1


def test_run_merge_bad_override_returns_1(tmp_path):
    args = _args(tmp_path, override="/nonexistent/override.json")
    rc = run_merge(args)
    assert rc == 1


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _build_parser():
    import argparse
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_parser(sub)
    return p


def test_add_parser_registers_merge_subcommand():
    p = _build_parser()
    ns = p.parse_args(["merge", "b.json", "o.json"])
    assert ns.base == "b.json"
    assert ns.override == "o.json"


def test_add_parser_default_dry_run_is_false():
    p = _build_parser()
    ns = p.parse_args(["merge", "b.json", "o.json"])
    assert ns.dry_run is False


def test_add_parser_sets_func_to_run_merge():
    p = _build_parser()
    ns = p.parse_args(["merge", "b.json", "o.json"])
    assert ns.func is run_merge
