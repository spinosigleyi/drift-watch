"""Tests for drift_watch/commands/pin_cmd.py."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from drift_watch.commands.pin_cmd import add_parser, _latest_snapshot, run_pin


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _args(
    service: str = "api",
    fields: list[str] | None = None,
    snapshot_dir: str = "snapshots",
    unpin: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        service=service,
        fields=fields,
        snapshot_dir=snapshot_dir,
        unpin=unpin,
    )


def _write_snapshot(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# add_parser
# ---------------------------------------------------------------------------

def _build_parser() -> tuple[argparse.ArgumentParser, argparse._SubParsersAction]:  # type: ignore[type-arg]
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    return parser, sub


def test_add_parser_registers_pin_subcommand():
    _, sub = _build_parser()
    add_parser(sub)
    ns = argparse.ArgumentParser().parse_args([])
    # just check it doesn't raise


def test_add_parser_default_unpin_is_false():
    parser, sub = _build_parser()
    add_parser(sub)
    ns = parser.parse_args(["pin", "svc"])
    assert ns.unpin is False


def test_add_parser_default_snapshot_dir():
    parser, sub = _build_parser()
    add_parser(sub)
    ns = parser.parse_args(["pin", "svc"])
    assert ns.snapshot_dir == "snapshots"


def test_add_parser_sets_func_to_run_pin():
    parser, sub = _build_parser()
    add_parser(sub)
    ns = parser.parse_args(["pin", "svc"])
    assert ns.func is run_pin


# ---------------------------------------------------------------------------
# _latest_snapshot
# ---------------------------------------------------------------------------

def test_latest_snapshot_returns_none_for_missing_dir(tmp_path):
    assert _latest_snapshot(tmp_path / "nonexistent") is None


def test_latest_snapshot_returns_most_recent(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text("{}")
    b.write_text("{}")
    # touch b to make it newer
    import time; time.sleep(0.01)
    b.write_text("{}")
    result = _latest_snapshot(tmp_path)
    assert result == b


# ---------------------------------------------------------------------------
# run_pin
# ---------------------------------------------------------------------------

def test_run_pin_no_snapshots_returns_1(tmp_path):
    rc = run_pin(_args(snapshot_dir=str(tmp_path)))
    assert rc == 1


def test_run_pin_unknown_service_returns_1(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"services": {"other": {"port": 80}}})
    rc = run_pin(_args(service="missing", snapshot_dir=str(tmp_path)))
    assert rc == 1


def test_run_pin_pins_all_fields(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"services": {"api": {"port": 8080, "env": "prod"}}})
    rc = run_pin(_args(service="api", snapshot_dir=str(tmp_path)))
    assert rc == 0
    data = json.loads(snap.read_text())
    assert data["pins"]["api"] == {"port": 8080, "env": "prod"}


def test_run_pin_pins_specific_fields(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"services": {"api": {"port": 8080, "env": "prod"}}})
    rc = run_pin(_args(service="api", fields=["port"], snapshot_dir=str(tmp_path)))
    assert rc == 0
    data = json.loads(snap.read_text())
    assert "port" in data["pins"]["api"]
    assert "env" not in data["pins"]["api"]


def test_run_unpin_removes_fields(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(
        snap,
        {"services": {"api": {"port": 8080}}, "pins": {"api": {"port": 8080, "env": "prod"}}},
    )
    rc = run_pin(_args(service="api", fields=["port"], snapshot_dir=str(tmp_path), unpin=True))
    assert rc == 0
    data = json.loads(snap.read_text())
    assert "port" not in data.get("pins", {}).get("api", {})


def test_run_unpin_removes_service_key_when_empty(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(
        snap,
        {"services": {"api": {"port": 8080}}, "pins": {"api": {"port": 8080}}},
    )
    rc = run_pin(_args(service="api", fields=["port"], snapshot_dir=str(tmp_path), unpin=True))
    assert rc == 0
    data = json.loads(snap.read_text())
    assert "api" not in data.get("pins", {})
