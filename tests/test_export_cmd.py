"""Tests for drift_watch/commands/export_cmd.py."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from drift_watch.commands.export_cmd import add_parser, run_export


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def declared_file(tmp_path: Path) -> Path:
    p = tmp_path / "declared.yaml"
    p.write_text("web:\n  replicas: 3\n  image: nginx:1.25\n")
    return p


@pytest.fixture()
def live_matching_file(tmp_path: Path) -> Path:
    p = tmp_path / "live_match.yaml"
    p.write_text("web:\n  replicas: 3\n  image: nginx:1.25\n")
    return p


@pytest.fixture()
def live_drifted_file(tmp_path: Path) -> Path:
    p = tmp_path / "live_drift.yaml"
    p.write_text("web:\n  replicas: 5\n  image: nginx:1.25\n")
    return p


def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        declared=None,
        live=None,
        output="/tmp/report.txt",
        format="text",
        fail_on_drift=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_add_parser_registers_export_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_parser(sub)
    args = root.parse_args(["export", "decl.yaml", "live.yaml", "-o", "out.txt"])
    assert args.func is run_export


def test_export_creates_text_file(declared_file, live_matching_file, tmp_path):
    out = tmp_path / "report.txt"
    args = _args(
        declared=str(declared_file),
        live=str(live_matching_file),
        output=str(out),
        format="text",
    )
    rc = run_export(args)
    assert rc == 0
    assert out.exists()
    assert "web" in out.read_text()


def test_export_creates_json_file(declared_file, live_matching_file, tmp_path):
    out = tmp_path / "report.json"
    args = _args(
        declared=str(declared_file),
        live=str(live_matching_file),
        output=str(out),
        format="json",
    )
    rc = run_export(args)
    assert rc == 0
    data = json.loads(out.read_text())
    assert isinstance(data, list)


def test_export_fail_on_drift_returns_1(declared_file, live_drifted_file, tmp_path):
    out = tmp_path / "report.txt"
    args = _args(
        declared=str(declared_file),
        live=str(live_drifted_file),
        output=str(out),
        fail_on_drift=True,
    )
    assert run_export(args) == 1


def test_export_no_fail_on_drift_returns_0(declared_file, live_drifted_file, tmp_path):
    out = tmp_path / "report.txt"
    args = _args(
        declared=str(declared_file),
        live=str(live_drifted_file),
        output=str(out),
        fail_on_drift=False,
    )
    assert run_export(args) == 0


def test_export_bad_declared_returns_1(tmp_path):
    out = tmp_path / "report.txt"
    args = _args(
        declared="nonexistent_declared.yaml",
        live="nonexistent_live.yaml",
        output=str(out),
    )
    assert run_export(args) == 1


def test_export_creates_parent_dirs(declared_file, live_matching_file, tmp_path):
    out = tmp_path / "nested" / "deep" / "report.txt"
    args = _args(
        declared=str(declared_file),
        live=str(live_matching_file),
        output=str(out),
    )
    rc = run_export(args)
    assert rc == 0
    assert out.exists()
