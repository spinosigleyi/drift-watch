"""Tests for drift_watch/commands/resolve_cmd.py."""
from __future__ import annotations

import json
import argparse
from pathlib import Path

import pytest

from drift_watch.commands.resolve_cmd import add_parser, _resolve_service, run_resolve


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _args(**kwargs):
    defaults = {
        "snapshot": "/tmp/snap.json",
        "service": "api",
        "fields": None,
        "note": "",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _write_snapshot(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# _resolve_service unit tests
# ---------------------------------------------------------------------------

def test_resolve_service_not_found():
    services: dict = {}
    found, resolved = _resolve_service(services, "missing", None, "", "2024-01-01T00:00:00+00:00")
    assert not found
    assert resolved == []


def test_resolve_all_drifted_fields():
    services = {"api": {"status": "drifted", "drifted_fields": ["replicas", "image"]}}
    found, resolved = _resolve_service(services, "api", None, "fixed", "2024-01-01T00:00:00+00:00")
    assert found
    assert set(resolved) == {"replicas", "image"}
    assert services["api"]["drifted_fields"] == []
    assert services["api"]["status"] == "ok"


def test_resolve_specific_field_only():
    services = {"api": {"status": "drifted", "drifted_fields": ["replicas", "image"]}}
    found, resolved = _resolve_service(services, "api", ["replicas"], "", "2024-01-01T00:00:00+00:00")
    assert resolved == ["replicas"]
    assert services["api"]["drifted_fields"] == ["image"]
    assert services["api"]["status"] == "drifted"  # still has image


def test_resolve_records_resolution_entry():
    services = {"api": {"status": "drifted", "drifted_fields": ["replicas"]}}
    _resolve_service(services, "api", None, "ticket-42", "2024-01-01T00:00:00+00:00")
    resolutions = services["api"]["resolutions"]
    assert len(resolutions) == 1
    assert resolutions[0]["field"] == "replicas"
    assert resolutions[0]["note"] == "ticket-42"


def test_resolve_unknown_field_is_noop():
    services = {"api": {"status": "drifted", "drifted_fields": ["image"]}}
    found, resolved = _resolve_service(services, "api", ["nonexistent"], "", "ts")
    assert found
    assert resolved == []
    assert services["api"]["drifted_fields"] == ["image"]


# ---------------------------------------------------------------------------
# run_resolve integration tests
# ---------------------------------------------------------------------------

def test_run_resolve_returns_zero_on_success(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"api": {"status": "drifted", "drifted_fields": ["replicas"]}})
    code = run_resolve(_args(snapshot=str(snap), service="api"))
    assert code == 0


def test_run_resolve_updates_file(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"api": {"status": "drifted", "drifted_fields": ["replicas"]}})
    run_resolve(_args(snapshot=str(snap), service="api"))
    data = json.loads(snap.read_text())
    assert data["api"]["drifted_fields"] == []
    assert data["api"]["status"] == "ok"


def test_run_resolve_missing_service_returns_1(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {})
    code = run_resolve(_args(snapshot=str(snap), service="ghost"))
    assert code == 1


def test_run_resolve_bad_snapshot_returns_1(tmp_path):
    snap = tmp_path / "snap.json"
    snap.write_text("not json{{{")
    code = run_resolve(_args(snapshot=str(snap), service="api"))
    assert code == 1


def test_add_parser_registers_resolve_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    ns = parser.parse_args(["resolve", "snap.json", "--service", "api"])
    assert ns.service == "api"
    assert ns.func is run_resolve
