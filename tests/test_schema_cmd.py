"""Tests for drift_watch/commands/schema_cmd.py."""
from __future__ import annotations

import json
from types import SimpleNamespace
from pathlib import Path

import pytest

from drift_watch.commands.schema_cmd import (
    _check_type,
    _load_schema,
    _validate_service,
    run_schema,
)
from drift_watch.loader import ConfigLoadError


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _args(live: str, schema: str, strict: bool = False) -> SimpleNamespace:
    return SimpleNamespace(live=live, schema=schema, strict=strict)


def _write_yaml(path: Path, content: str) -> str:
    path.write_text(content, encoding="utf-8")
    return str(path)


def _write_schema(path: Path, schema: dict) -> str:
    path.write_text(json.dumps(schema), encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# _check_type
# ---------------------------------------------------------------------------

def test_check_type_string_ok():
    assert _check_type("hello", "string") is True


def test_check_type_string_fail():
    assert _check_type(42, "string") is False


def test_check_type_unknown_type_passes():
    assert _check_type(object(), "custom") is True


# ---------------------------------------------------------------------------
# _validate_service
# ---------------------------------------------------------------------------

def test_validate_service_no_issues():
    schema = {"required": ["port"], "properties": {"port": {"type": "integer"}}}
    issues = _validate_service("svc", {"port": 8080}, schema)
    assert issues == []


def test_validate_service_missing_required():
    schema = {"required": ["port"], "properties": {}}
    issues = _validate_service("svc", {}, schema)
    assert len(issues) == 1
    assert issues[0]["level"] == "error"
    assert "port" in issues[0]["message"]


def test_validate_service_wrong_type():
    schema = {"required": [], "properties": {"port": {"type": "integer"}}}
    issues = _validate_service("svc", {"port": "not-an-int"}, schema)
    assert any(i["level"] == "error" for i in issues)


def test_validate_service_enum_warning():
    schema = {"required": [], "properties": {"env": {"enum": ["prod", "staging"]}}}
    issues = _validate_service("svc", {"env": "dev"}, schema)
    assert any(i["level"] == "warning" for i in issues)


# ---------------------------------------------------------------------------
# run_schema integration
# ---------------------------------------------------------------------------

def test_run_schema_passes_clean(tmp_path):
    live = _write_yaml(tmp_path / "live.yaml",
                       "api:\n  port: 8080\n  env: prod\n")
    schema = _write_schema(tmp_path / "schema.json", {
        "required": ["port"],
        "properties": {"port": {"type": "integer"}, "env": {"enum": ["prod", "staging"]}},
    })
    assert run_schema(_args(live, schema)) == 0


def test_run_schema_returns_1_on_missing_required(tmp_path):
    live = _write_yaml(tmp_path / "live.yaml", "api:\n  env: prod\n")
    schema = _write_schema(tmp_path / "schema.json", {
        "required": ["port"], "properties": {},
    })
    assert run_schema(_args(live, schema)) == 1


def test_run_schema_strict_returns_1_on_warning(tmp_path):
    live = _write_yaml(tmp_path / "live.yaml", "api:\n  env: dev\n")
    schema = _write_schema(tmp_path / "schema.json", {
        "required": [],
        "properties": {"env": {"enum": ["prod", "staging"]}},
    })
    assert run_schema(_args(live, schema, strict=True)) == 1


def test_run_schema_non_strict_warning_exits_zero(tmp_path):
    live = _write_yaml(tmp_path / "live.yaml", "api:\n  env: dev\n")
    schema = _write_schema(tmp_path / "schema.json", {
        "required": [],
        "properties": {"env": {"enum": ["prod", "staging"]}},
    })
    assert run_schema(_args(live, schema, strict=False)) == 0


def test_run_schema_missing_live_file_returns_1(tmp_path):
    schema = _write_schema(tmp_path / "schema.json", {})
    assert run_schema(_args(str(tmp_path / "nope.yaml"), schema)) == 1


def test_run_schema_missing_schema_file_returns_1(tmp_path):
    live = _write_yaml(tmp_path / "live.yaml", "api:\n  port: 8080\n")
    assert run_schema(_args(live, str(tmp_path / "nope.json"))) == 1
