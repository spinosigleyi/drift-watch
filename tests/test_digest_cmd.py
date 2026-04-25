"""Tests for drift_watch/commands/digest_cmd.py."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from drift_watch.commands.digest_cmd import add_parser, _compute_digest, run_digest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_snapshot(path: Path, services: dict | None = None) -> Path:
    payload = {
        "timestamp": "2024-01-01T00:00:00",
        "services": services or {"svc-a": {"image": "nginx:1.25"}},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _args(tmp_path: Path, snapshot: str = "", short: bool = False, json_output: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        snapshot=snapshot or str(tmp_path / "snap.json"),
        short=short,
        json_output=json_output,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    return parser


# ---------------------------------------------------------------------------
# _compute_digest
# ---------------------------------------------------------------------------

def test_compute_digest_returns_64_char_hex(tmp_path: Path) -> None:
    p = _write_snapshot(tmp_path / "snap.json")
    digest = _compute_digest(p)
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_compute_digest_deterministic(tmp_path: Path) -> None:
    p = _write_snapshot(tmp_path / "snap.json")
    assert _compute_digest(p) == _compute_digest(p)


def test_compute_digest_differs_for_different_content(tmp_path: Path) -> None:
    p1 = _write_snapshot(tmp_path / "a.json", services={"svc-a": {"image": "nginx:1.25"}})
    p2 = _write_snapshot(tmp_path / "b.json", services={"svc-b": {"image": "redis:7"}})
    assert _compute_digest(p1) != _compute_digest(p2)


# ---------------------------------------------------------------------------
# run_digest
# ---------------------------------------------------------------------------

def test_run_digest_returns_zero_on_success(tmp_path: Path, capsys) -> None:
    snap = _write_snapshot(tmp_path / "snap.json")
    code = run_digest(_args(tmp_path, snapshot=str(snap)))
    assert code == 0


def test_run_digest_prints_full_digest_by_default(tmp_path: Path, capsys) -> None:
    snap = _write_snapshot(tmp_path / "snap.json")
    run_digest(_args(tmp_path, snapshot=str(snap)))
    out = capsys.readouterr().out
    # Full SHA-256 is 64 hex chars
    assert len(out.split()[0]) == 64


def test_run_digest_short_flag_prints_12_chars(tmp_path: Path, capsys) -> None:
    snap = _write_snapshot(tmp_path / "snap.json")
    run_digest(_args(tmp_path, snapshot=str(snap), short=True))
    out = capsys.readouterr().out
    assert len(out.split()[0]) == 12


def test_run_digest_json_output(tmp_path: Path, capsys) -> None:
    snap = _write_snapshot(tmp_path / "snap.json")
    run_digest(_args(tmp_path, snapshot=str(snap), json_output=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "digest" in data
    assert "path" in data
    assert data["short"] is False


def test_run_digest_missing_file_returns_one(tmp_path: Path, capsys) -> None:
    code = run_digest(_args(tmp_path, snapshot=str(tmp_path / "missing.json")))
    assert code == 1
    assert "not found" in capsys.readouterr().out


def test_run_digest_bad_snapshot_returns_one(tmp_path: Path, capsys) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{\"not\": \"a snapshot\"}", encoding="utf-8")
    code = run_digest(_args(tmp_path, snapshot=str(bad)))
    assert code == 1


# ---------------------------------------------------------------------------
# add_parser
# ---------------------------------------------------------------------------

def test_add_parser_registers_digest_subcommand() -> None:
    parser = _build_parser()
    ns = parser.parse_args(["digest", "/some/file.json"])
    assert ns.snapshot == "/some/file.json"


def test_add_parser_sets_func_to_run_digest() -> None:
    parser = _build_parser()
    ns = parser.parse_args(["digest", "/some/file.json"])
    assert ns.func is run_digest


def test_add_parser_default_short_is_false() -> None:
    parser = _build_parser()
    ns = parser.parse_args(["digest", "/some/file.json"])
    assert ns.short is False


def test_add_parser_short_flag() -> None:
    parser = _build_parser()
    ns = parser.parse_args(["digest", "/some/file.json", "--short"])
    assert ns.short is True


def test_add_parser_json_flag() -> None:
    parser = _build_parser()
    ns = parser.parse_args(["digest", "/some/file.json", "--json"])
    assert ns.json_output is True
