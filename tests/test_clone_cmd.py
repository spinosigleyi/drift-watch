"""Tests for drift_watch/commands/clone_cmd.py."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from drift_watch.commands.clone_cmd import add_parser, run_clone


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_snapshot(path: Path, services: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump({"services": services}, fh)


def _args(**kwargs):
    defaults = dict(
        source="src.json",
        destination="dst.json",
        service="svc-a",
        rename=None,
        overwrite=False,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# parser tests
# ---------------------------------------------------------------------------

def _build_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    return parser


def test_add_parser_registers_clone_subcommand():
    parser = _build_parser()
    ns = parser.parse_args(["clone", "src.json", "dst.json", "svc-a"])
    assert ns.source == "src.json"
    assert ns.destination == "dst.json"
    assert ns.service == "svc-a"


def test_add_parser_default_rename_is_none():
    parser = _build_parser()
    ns = parser.parse_args(["clone", "src.json", "dst.json", "svc-a"])
    assert ns.rename is None


def test_add_parser_default_overwrite_is_false():
    parser = _build_parser()
    ns = parser.parse_args(["clone", "src.json", "dst.json", "svc-a"])
    assert ns.overwrite is False


def test_add_parser_sets_func_to_run_clone():
    parser = _build_parser()
    ns = parser.parse_args(["clone", "src.json", "dst.json", "svc-a"])
    assert ns.func is run_clone


# ---------------------------------------------------------------------------
# run_clone tests
# ---------------------------------------------------------------------------

def test_clone_missing_source_returns_1(tmp_path):
    args = _args(source=str(tmp_path / "nope.json"), destination=str(tmp_path / "dst.json"))
    assert run_clone(args) == 1


def test_clone_service_not_in_source_returns_1(tmp_path):
    src = tmp_path / "src.json"
    _write_snapshot(src, {"other-svc": {"port": 80}})
    args = _args(source=str(src), destination=str(tmp_path / "dst.json"), service="missing")
    assert run_clone(args) == 1


def test_clone_creates_destination_if_missing(tmp_path):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    _write_snapshot(src, {"svc-a": {"port": 8080}})
    args = _args(source=str(src), destination=str(dst))
    rc = run_clone(args)
    assert rc == 0
    assert dst.exists()
    data = json.loads(dst.read_text())
    assert "svc-a" in data["services"]


def test_clone_rename_stores_under_new_name(tmp_path):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    _write_snapshot(src, {"svc-a": {"port": 8080}})
    args = _args(source=str(src), destination=str(dst), rename="svc-b")
    assert run_clone(args) == 0
    data = json.loads(dst.read_text())
    assert "svc-b" in data["services"]
    assert "svc-a" not in data["services"]


def test_clone_no_overwrite_returns_1_when_exists(tmp_path):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    _write_snapshot(src, {"svc-a": {"port": 8080}})
    _write_snapshot(dst, {"svc-a": {"port": 9090}})
    args = _args(source=str(src), destination=str(dst), overwrite=False)
    assert run_clone(args) == 1


def test_clone_overwrite_replaces_service(tmp_path):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    _write_snapshot(src, {"svc-a": {"port": 8080}})
    _write_snapshot(dst, {"svc-a": {"port": 9090}})
    args = _args(source=str(src), destination=str(dst), overwrite=True)
    assert run_clone(args) == 0
    data = json.loads(dst.read_text())
    assert data["services"]["svc-a"]["port"] == 8080


def test_clone_preserves_existing_services_in_destination(tmp_path):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    _write_snapshot(src, {"svc-a": {"port": 8080}})
    _write_snapshot(dst, {"svc-z": {"port": 5000}})
    args = _args(source=str(src), destination=str(dst))
    assert run_clone(args) == 0
    data = json.loads(dst.read_text())
    assert "svc-z" in data["services"]
    assert "svc-a" in data["services"]
