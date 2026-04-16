"""Tests for drift_watch/commands/tag_cmd.py"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from drift_watch.commands.tag_cmd import _parse_tags, add_parser, run_tag


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _args(snapshot: str, tags: list[str]) -> argparse.Namespace:
    return argparse.Namespace(snapshot=snapshot, tags=tags)


def _write_snapshot(path: Path, extra: dict | None = None) -> None:
    data = {"services": {"svc": {"replicas": 2}}, **(extra or {})}
    path.write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# _parse_tags
# ---------------------------------------------------------------------------

def test_parse_tags_single():
    assert _parse_tags(["env=prod"]) == {"env": "prod"}


def test_parse_tags_multiple():
    assert _parse_tags(["env=prod", "team=platform"]) == {"env": "prod", "team": "platform"}


def test_parse_tags_missing_equals_raises():
    with pytest.raises(ValueError, match="KEY=VALUE"):
        _parse_tags(["noequalssign"])


def test_parse_tags_empty_key_raises():
    with pytest.raises(ValueError, match="empty"):
        _parse_tags(["=value"])


# ---------------------------------------------------------------------------
# run_tag
# ---------------------------------------------------------------------------

def test_run_tag_returns_zero_on_success(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap)
    assert run_tag(_args(str(snap), ["env=staging"])) == 0


def test_run_tag_writes_tags(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap)
    run_tag(_args(str(snap), ["env=prod", "team=ops"]))
    data = json.loads(snap.read_text())
    assert data["tags"] == {"env": "prod", "team": "ops"}


def test_run_tag_merges_existing_tags(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"tags": {"env": "dev"}})
    run_tag(_args(str(snap), ["team=sre"]))
    data = json.loads(snap.read_text())
    assert data["tags"] == {"env": "dev", "team": "sre"}


def test_run_tag_overwrites_existing_key(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, {"tags": {"env": "dev"}})
    run_tag(_args(str(snap), ["env=prod"]))
    data = json.loads(snap.read_text())
    assert data["tags"]["env"] == "prod"


def test_run_tag_missing_file_returns_1(tmp_path):
    assert run_tag(_args(str(tmp_path / "missing.json"), ["env=x"])) == 1


def test_run_tag_bad_tag_returns_1(tmp_path):
    snap = tmp_path / "snap.json"
    _write_snapshot(snap)
    assert run_tag(_args(str(snap), ["badtag"])) == 1


def test_add_parser_registers_tag_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_parser(sub)
    ns = root.parse_args(["tag", "snap.json", "env=prod"])
    assert ns.snapshot == "snap.json"
    assert ns.tags == ["env=prod"]
    assert ns.func is run_tag
