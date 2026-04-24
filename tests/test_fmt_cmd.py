"""Tests for drift_watch/commands/fmt_cmd.py."""
from __future__ import annotations

import json
import pathlib
import types

import pytest

from drift_watch.commands.fmt_cmd import _canonical, add_parser, run_fmt


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _args(
    snapshot_dir: str = "snapshots",
    check: bool = False,
    indent: int = 2,
) -> types.SimpleNamespace:
    return types.SimpleNamespace(snapshot_dir=snapshot_dir, check=check, indent=indent)


def _write_snapshot(path: pathlib.Path, data: dict) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")  # NOT pretty-printed
    return path


# ---------------------------------------------------------------------------
# _canonical
# ---------------------------------------------------------------------------

def test_canonical_sorts_keys():
    result = _canonical({"b": 1, "a": 2}, indent=2)
    parsed = json.loads(result)
    assert list(parsed.keys()) == ["a", "b"]


def test_canonical_ends_with_newline():
    assert _canonical({}, 2).endswith("\n")


def test_canonical_respects_indent():
    result = _canonical({"x": 1}, indent=4)
    assert "    " in result


# ---------------------------------------------------------------------------
# run_fmt
# ---------------------------------------------------------------------------

def test_missing_dir_returns_one(tmp_path):
    rc = run_fmt(_args(snapshot_dir=str(tmp_path / "no_such_dir")))
    assert rc == 1


def test_empty_dir_returns_zero(tmp_path):
    rc = run_fmt(_args(snapshot_dir=str(tmp_path)))
    assert rc == 0


def test_already_canonical_reports_zero(tmp_path):
    data = {"services": {}}
    path = tmp_path / "snap.json"
    path.write_text(_canonical(data, 2), encoding="utf-8")
    rc = run_fmt(_args(snapshot_dir=str(tmp_path)))
    assert rc == 0


def test_reformats_file_in_place(tmp_path):
    data = {"z": 1, "a": 2}
    path = tmp_path / "snap.json"
    _write_snapshot(path, data)  # compact, unsorted
    rc = run_fmt(_args(snapshot_dir=str(tmp_path)))
    assert rc == 0
    written = json.loads(path.read_text(encoding="utf-8"))
    assert list(written.keys()) == ["a", "z"]


def test_check_mode_does_not_write(tmp_path):
    data = {"z": 1, "a": 2}
    path = tmp_path / "snap.json"
    original = json.dumps(data)
    path.write_text(original, encoding="utf-8")
    rc = run_fmt(_args(snapshot_dir=str(tmp_path), check=True))
    assert rc == 1
    assert path.read_text(encoding="utf-8") == original


def test_check_mode_returns_zero_when_already_canonical(tmp_path):
    data = {"a": 1}
    path = tmp_path / "snap.json"
    path.write_text(_canonical(data, 2), encoding="utf-8")
    rc = run_fmt(_args(snapshot_dir=str(tmp_path), check=True))
    assert rc == 0


def test_invalid_json_returns_one(tmp_path):
    (tmp_path / "bad.json").write_text("not json", encoding="utf-8")
    rc = run_fmt(_args(snapshot_dir=str(tmp_path)))
    assert rc == 1


def test_multiple_files_all_reformatted(tmp_path):
    for name in ("a.json", "b.json", "c.json"):
        _write_snapshot(tmp_path / name, {"key": name})
    rc = run_fmt(_args(snapshot_dir=str(tmp_path)))
    assert rc == 0
    for name in ("a.json", "b.json", "c.json"):
        raw = (tmp_path / name).read_text(encoding="utf-8")
        assert raw == _canonical({"key": name}, 2)


# ---------------------------------------------------------------------------
# add_parser
# ---------------------------------------------------------------------------

def _build_parser():
    import argparse
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_parser(sub)
    return p


def test_add_parser_registers_fmt_subcommand():
    p = _build_parser()
    ns = p.parse_args(["fmt"])
    assert hasattr(ns, "func")


def test_add_parser_sets_func_to_run_fmt():
    p = _build_parser()
    ns = p.parse_args(["fmt"])
    assert ns.func is run_fmt


def test_add_parser_default_snapshot_dir():
    p = _build_parser()
    ns = p.parse_args(["fmt"])
    assert ns.snapshot_dir == "snapshots"


def test_add_parser_check_flag():
    p = _build_parser()
    ns = p.parse_args(["fmt", "--check"])
    assert ns.check is True


def test_add_parser_indent_flag():
    p = _build_parser()
    ns = p.parse_args(["fmt", "--indent", "4"])
    assert ns.indent == 4
