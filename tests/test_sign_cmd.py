"""Tests for drift_watch/commands/sign_cmd.py."""
from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from drift_watch.commands.sign_cmd import (
    _SIG_KEY,
    _canonical_bytes,
    _compute_sig,
    _load_raw,
    run_sign,
)

_SECRET = "test-secret-key"


def _write_snapshot(tmp_path: Path, data: dict) -> Path:  # type: ignore[type-arg]
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(data, indent=2))
    return p


def _args(snapshot: str, verify: bool = False, key_env: str = "DW_TEST_KEY") -> SimpleNamespace:
    return SimpleNamespace(snapshot=snapshot, verify=verify, key_env=key_env)


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("DW_TEST_KEY", _SECRET)


# ---------------------------------------------------------------------------
# unit helpers
# ---------------------------------------------------------------------------

def test_canonical_bytes_excludes_signature():
    data = {"a": 1, _SIG_KEY: "old-sig"}
    result = _canonical_bytes(data)
    assert _SIG_KEY.encode() not in result
    assert b'"a"' in result


def test_compute_sig_is_deterministic():
    data = {"services": {"svc": {"replicas": 2}}}
    assert _compute_sig(data, _SECRET) == _compute_sig(data, _SECRET)


def test_compute_sig_changes_with_data():
    d1 = {"x": 1}
    d2 = {"x": 2}
    assert _compute_sig(d1, _SECRET) != _compute_sig(d2, _SECRET)


def test_compute_sig_changes_with_secret():
    data = {"x": 1}
    assert _compute_sig(data, "secret-a") != _compute_sig(data, "secret-b")


# ---------------------------------------------------------------------------
# run_sign — signing
# ---------------------------------------------------------------------------

def test_run_sign_creates_signature(tmp_path):
    snap = _write_snapshot(tmp_path, {"services": {}})
    rc = run_sign(_args(str(snap)))
    assert rc == 0
    saved = json.loads(snap.read_text())
    assert _SIG_KEY in saved
    assert len(saved[_SIG_KEY]) == 64  # sha256 hex


def test_run_sign_missing_file_returns_1(tmp_path):
    rc = run_sign(_args(str(tmp_path / "missing.json")))
    assert rc == 1


def test_run_sign_missing_env_returns_1(tmp_path, monkeypatch):
    monkeypatch.delenv("DW_TEST_KEY", raising=False)
    snap = _write_snapshot(tmp_path, {"services": {}})
    rc = run_sign(_args(str(snap)))
    assert rc == 1


def test_run_sign_overwrites_old_signature(tmp_path):
    snap = _write_snapshot(tmp_path, {"services": {}, _SIG_KEY: "stale"})
    run_sign(_args(str(snap)))
    saved = json.loads(snap.read_text())
    assert saved[_SIG_KEY] != "stale"


# ---------------------------------------------------------------------------
# run_sign — verification
# ---------------------------------------------------------------------------

def test_run_verify_valid_signature(tmp_path):
    snap = _write_snapshot(tmp_path, {"services": {}})
    run_sign(_args(str(snap)))  # sign first
    rc = run_sign(_args(str(snap), verify=True))
    assert rc == 0


def test_run_verify_tampered_file_returns_1(tmp_path):
    snap = _write_snapshot(tmp_path, {"services": {}})
    run_sign(_args(str(snap)))
    data = json.loads(snap.read_text())
    data["injected"] = "evil"
    snap.write_text(json.dumps(data))
    rc = run_sign(_args(str(snap), verify=True))
    assert rc == 1


def test_run_verify_missing_signature_returns_1(tmp_path):
    snap = _write_snapshot(tmp_path, {"services": {}})
    rc = run_sign(_args(str(snap), verify=True))
    assert rc == 1
