"""Tests for drift_watch/commands/report_cmd.py"""
from __future__ import annotations

import json
import argparse
from pathlib import Path

import pytest

from drift_watch.commands.report_cmd import (
    add_parser,
    _collect_report,
    _format_text,
    run_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _args(**kwargs):
    defaults = {"snapshot_dir": "snapshots", "output": "text", "out_file": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _write_snapshot(directory: Path, name: str, payload: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(json.dumps(payload), encoding="utf-8")


# ---------------------------------------------------------------------------
# _collect_report
# ---------------------------------------------------------------------------

def test_collect_missing_dir_returns_zeros(tmp_path):
    result = _collect_report(str(tmp_path / "no_such_dir"))
    assert result["snapshots"] == 0
    assert result["total_drifted"] == 0
    assert result["services"] == {}


def test_collect_counts_snapshots(tmp_path):
    snap = {"svc-a": {"status": "ok"}}
    _write_snapshot(tmp_path, "s1.json", snap)
    _write_snapshot(tmp_path, "s2.json", snap)
    result = _collect_report(str(tmp_path))
    assert result["snapshots"] == 2


def test_collect_tracks_drift(tmp_path):
    _write_snapshot(tmp_path, "s1.json", {"svc-a": {"status": "drifted"}})
    _write_snapshot(tmp_path, "s2.json", {"svc-a": {"status": "ok"}})
    result = _collect_report(str(tmp_path))
    assert result["services"]["svc-a"]["drift_count"] == 1
    assert result["services"]["svc-a"]["ok_count"] == 1
    assert result["total_drifted"] == 1


def test_collect_missing_status_counts_as_ok(tmp_path):
    _write_snapshot(tmp_path, "s1.json", {"svc-b": {"fields": []}})
    result = _collect_report(str(tmp_path))
    assert result["services"]["svc-b"]["ok_count"] == 1


def test_collect_ignores_bad_json(tmp_path):
    (tmp_path / "bad.json").write_text("NOT JSON", encoding="utf-8")
    result = _collect_report(str(tmp_path))
    assert result["snapshots"] == 0


# ---------------------------------------------------------------------------
# _format_text
# ---------------------------------------------------------------------------

def test_format_text_shows_summary():
    data = {"snapshots": 3, "services": {}, "total_drifted": 0}
    text = _format_text(data)
    assert "Snapshots scanned" in text
    assert "3" in text


def test_format_text_lists_services():
    data = {
        "snapshots": 1,
        "total_drifted": 1,
        "services": {"api": {"appearances": 1, "drift_count": 1, "ok_count": 0}},
    }
    text = _format_text(data)
    assert "api" in text


# ---------------------------------------------------------------------------
# run_report
# ---------------------------------------------------------------------------

def test_run_report_text_returns_zero(tmp_path, capsys):
    _write_snapshot(tmp_path, "s1.json", {"svc": {"status": "ok"}})
    rc = run_report(_args(snapshot_dir=str(tmp_path)))
    assert rc == 0
    captured = capsys.readouterr()
    assert "Snapshots scanned" in captured.out


def test_run_report_json_output(tmp_path, capsys):
    _write_snapshot(tmp_path, "s1.json", {"svc": {"status": "ok"}})
    rc = run_report(_args(snapshot_dir=str(tmp_path), output="json"))
    assert rc == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "snapshots" in parsed


def test_run_report_writes_to_file(tmp_path):
    _write_snapshot(tmp_path, "s1.json", {"svc": {"status": "ok"}})
    out_file = tmp_path / "report.txt"
    rc = run_report(_args(snapshot_dir=str(tmp_path), out_file=str(out_file)))
    assert rc == 0
    assert out_file.exists()
    assert "Snapshots scanned" in out_file.read_text()


def test_run_report_bad_out_file_returns_one(tmp_path):
    rc = run_report(_args(snapshot_dir=str(tmp_path), out_file="/no/such/dir/out.txt"))
    assert rc == 1


# ---------------------------------------------------------------------------
# add_parser
# ---------------------------------------------------------------------------

def test_add_parser_registers_report_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    ns = parser.parse_args(["report"])
    assert ns.func is run_report


def test_add_parser_default_output_is_text():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    ns = parser.parse_args(["report"])
    assert ns.output == "text"
