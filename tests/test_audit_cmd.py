"""Tests for drift_watch/commands/audit_cmd.py."""
from __future__ import annotations

import json
import os
from argparse import Namespace
from types import SimpleNamespace

import pytest

from drift_watch.commands.audit_cmd import (
    _collect_audit_entries,
    run_audit,
    add_parser,
)


def _args(**kwargs):
    defaults = {
        "service": "api",
        "snapshot_dir": "snapshots",
        "limit": 10,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _write_snapshot(directory: str, filename: str, data: dict) -> None:
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, filename), "w", encoding="utf-8") as fh:
        json.dump(data, fh)


# ---------------------------------------------------------------------------
# _collect_audit_entries
# ---------------------------------------------------------------------------

def test_collect_returns_empty_for_missing_dir(tmp_path):
    result = _collect_audit_entries(str(tmp_path / "no_such_dir"), "api", 10)
    assert result == []


def test_collect_finds_service_in_snapshot(tmp_path):
    snap_dir = str(tmp_path / "snaps")
    _write_snapshot(
        snap_dir,
        "2024-01-01.json",
        {"timestamp": "2024-01-01T00:00:00", "services": {"api": {"port": 8080}}},
    )
    result = _collect_audit_entries(snap_dir, "api", 10)
    assert len(result) == 1
    assert result[0]["config"] == {"port": 8080}


def test_collect_ignores_missing_service(tmp_path):
    snap_dir = str(tmp_path / "snaps")
    _write_snapshot(
        snap_dir,
        "2024-01-01.json",
        {"timestamp": "2024-01-01T00:00:00", "services": {"other": {"port": 9090}}},
    )
    result = _collect_audit_entries(snap_dir, "api", 10)
    assert result == []


def test_collect_respects_limit(tmp_path):
    snap_dir = str(tmp_path / "snaps")
    for i in range(5):
        _write_snapshot(
            snap_dir,
            f"2024-01-0{i+1}.json",
            {"timestamp": f"2024-01-0{i+1}T00:00:00", "services": {"api": {"port": 8000 + i}}},
        )
    result = _collect_audit_entries(snap_dir, "api", 3)
    assert len(result) == 3


def test_collect_skips_malformed_json(tmp_path):
    snap_dir = str(tmp_path / "snaps")
    bad_path = os.path.join(snap_dir, "bad.json")
    os.makedirs(snap_dir, exist_ok=True)
    with open(bad_path, "w") as fh:
        fh.write("not valid json")
    result = _collect_audit_entries(snap_dir, "api", 10)
    assert result == []


# ---------------------------------------------------------------------------
# run_audit
# ---------------------------------------------------------------------------

def test_run_audit_returns_zero_no_history(tmp_path, capsys):
    code = run_audit(_args(snapshot_dir=str(tmp_path / "empty"), service="api"))
    assert code == 0
    captured = capsys.readouterr()
    assert "No audit history" in captured.out


def test_run_audit_prints_entries(tmp_path, capsys):
    snap_dir = str(tmp_path / "snaps")
    _write_snapshot(
        snap_dir,
        "2024-06-01.json",
        {"timestamp": "2024-06-01T12:00:00", "services": {"api": {"port": 443}}},
    )
    code = run_audit(_args(snapshot_dir=snap_dir, service="api", limit=10))
    assert code == 0
    out = capsys.readouterr().out
    assert "api" in out
    assert "port" in out


# ---------------------------------------------------------------------------
# add_parser
# ---------------------------------------------------------------------------

def test_add_parser_registers_audit_subcommand():
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    args = parser.parse_args(["audit", "my-service"])
    assert args.service == "my-service"


def test_add_parser_default_limit():
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    args = parser.parse_args(["audit", "svc"])
    assert args.limit == 10


def test_add_parser_sets_func_to_run_audit():
    import argparse
    from drift_watch.commands.audit_cmd import run_audit
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    args = parser.parse_args(["audit", "svc"])
    assert args.func is run_audit
