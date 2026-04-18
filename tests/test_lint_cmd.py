"""Tests for lint_cmd."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

from drift_watch.commands.lint_cmd import _lint_config, run_lint


def _args(declared: str, strict: bool = False) -> SimpleNamespace:
    return SimpleNamespace(declared=declared, strict=strict)


# ── _lint_config unit tests ──────────────────────────────────────────────────

def test_lint_clean_config_returns_no_issues():
    config = {"svc": {"port": 8080, "env": "prod"}}
    assert _lint_config(config) == []


def test_lint_empty_fields_is_warning():
    issues = _lint_config({"svc": {}})
    assert any(lvl == "warning" and "no fields" in msg for lvl, msg in issues)


def test_lint_null_value_is_warning():
    issues = _lint_config({"svc": {"port": None}})
    assert any(lvl == "warning" and "null" in msg for lvl, msg in issues)


def test_lint_whitespace_key_is_error():
    issues = _lint_config({"svc": {" port": 8080}})
    assert any(lvl == "error" and "whitespace" in msg for lvl, msg in issues)


def test_lint_non_mapping_service_is_error():
    issues = _lint_config({"svc": "not-a-dict"})
    assert any(lvl == "error" and "mapping" in msg for lvl, msg in issues)


# ── run_lint integration tests ───────────────────────────────────────────────

def test_run_lint_ok_returns_zero(tmp_path):
    f = tmp_path / "declared.yaml"
    f.write_text("svc:\n  port: 8080\n")
    assert run_lint(_args(str(f))) == 0


def test_run_lint_warning_returns_zero_without_strict(tmp_path):
    f = tmp_path / "declared.yaml"
    f.write_text("svc:\n  port: null\n")
    assert run_lint(_args(str(f), strict=False)) == 0


def test_run_lint_warning_returns_one_with_strict(tmp_path):
    f = tmp_path / "declared.yaml"
    f.write_text("svc:\n  port: null\n")
    assert run_lint(_args(str(f), strict=True)) == 1


def test_run_lint_error_returns_one(tmp_path):
    f = tmp_path / "declared.yaml"
    f.write_text("svc:\n  ' port': 8080\n")
    assert run_lint(_args(str(f))) == 1


def test_run_lint_missing_file_returns_one(tmp_path):
    assert run_lint(_args(str(tmp_path / "missing.yaml"))) == 1


def test_run_lint_json_file(tmp_path):
    f = tmp_path / "declared.json"
    f.write_text(json.dumps({"api": {"host": "localhost"}}))
    assert run_lint(_args(str(f))) == 0
