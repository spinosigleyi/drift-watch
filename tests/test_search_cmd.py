"""Tests for search_cmd."""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from drift_watch.commands.search_cmd import add_parser, _collect_matches, run_search


def _args(tmp_path, pattern="*", drifted_only=False):
    return types.SimpleNamespace(
        pattern=pattern,
        snapshot_dir=str(tmp_path),
        drifted_only=drifted_only,
    )


def _write_snapshot(directory: Path, name: str, services: dict):
    path = directory / name
    path.write_text(json.dumps({"services": services}))
    return path


def test_collect_returns_empty_for_missing_dir(tmp_path):
    results = _collect_matches(str(tmp_path / "nope"), "*", False)
    assert results == []


def test_collect_finds_matching_service(tmp_path):
    _write_snapshot(tmp_path, "snap1.json", {"api": {"status": "ok"}})
    results = _collect_matches(str(tmp_path), "api", False)
    assert len(results) == 1
    assert results[0][1] == "api"


def test_collect_glob_pattern(tmp_path):
    _write_snapshot(tmp_path, "snap1.json", {"api-v1": {"status": "ok"}, "db": {"status": "ok"}})
    results = _collect_matches(str(tmp_path), "api-*", False)
    assert len(results) == 1
    assert results[0][1] == "api-v1"


def test_collect_drifted_only_filters(tmp_path):
    _write_snapshot(
        tmp_path, "snap1.json",
        {"api": {"status": "ok"}, "worker": {"status": "drifted"}},
    )
    results = _collect_matches(str(tmp_path), "*", drifted_only=True)
    assert len(results) == 1
    assert results[0][1] == "worker"


def test_collect_skips_malformed_json(tmp_path):
    (tmp_path / "bad.json").write_text("not json")
    results = _collect_matches(str(tmp_path), "*", False)
    assert results == []


def test_collect_multiple_snapshots(tmp_path):
    _write_snapshot(tmp_path, "a.json", {"svc": {"status": "ok"}})
    _write_snapshot(tmp_path, "b.json", {"svc": {"status": "drifted"}})
    results = _collect_matches(str(tmp_path), "svc", False)
    assert len(results) == 2


def test_run_search_no_matches_returns_zero(tmp_path, capsys):
    args = _args(tmp_path, pattern="nonexistent")
    rc = run_search(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No matching" in out


def test_run_search_prints_results(tmp_path, capsys):
    _write_snapshot(tmp_path, "snap.json", {"api": {"status": "drifted"}})
    args = _args(tmp_path, pattern="api")
    rc = run_search(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "api" in out
    assert "drifted" in out


def test_add_parser_registers_search_subcommand():
    import argparse
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_parser(sub)
    args = root.parse_args(["search", "api-*"])
    assert args.pattern == "api-*"
    assert args.drifted_only is False
