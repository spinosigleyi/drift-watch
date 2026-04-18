"""Tests for drift_watch/commands/validate_cmd.py"""
from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

import pytest

from drift_watch.commands.validate_cmd import (
    _validate_structure,
    add_parser,
    run_validate,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _args(tmp_path: Path, declared: str, strict: bool = False) -> argparse.Namespace:
    p = tmp_path / "declared.yaml"
    p.write_text(declared)
    return argparse.Namespace(declared=str(p), strict=strict)


# ---------------------------------------------------------------------------
# _validate_structure
# ---------------------------------------------------------------------------

def test_validate_clean_config_returns_no_issues():
    config = {"svc": {"port": 8080, "replicas": 2}}
    assert _validate_structure(config) == []


def test_validate_empty_config_returns_warning():
    issues = _validate_structure({})
    assert len(issues) == 1
    assert issues[0]["level"] == "warning"


def test_validate_non_mapping_service_is_error():
    issues = _validate_structure({"svc": ["not", "a", "dict"]})
    assert any(i["level"] == "error" for i in issues)


def test_validate_empty_fields_is_warning():
    issues = _validate_structure({"svc": {}})
    assert any(i["level"] == "warning" and "no fields" in i["message"] for i in issues)


def test_validate_null_value_is_warning():
    issues = _validate_structure({"svc": {"key": None}})
    assert any(i["level"] == "warning" and "null" in i["message"] for i in issues)


def test_validate_blank_key_is_error():
    issues = _validate_structure({"svc": {"  ": "val"}})
    assert any(i["level"] == "error" and "blank" in i["message"] for i in issues)


# ---------------------------------------------------------------------------
# run_validate
# ---------------------------------------------------------------------------

def test_run_validate_returns_zero_on_clean(tmp_path):
    ns = _args(tmp_path, "svc:\n  port: 8080\n")
    assert run_validate(ns) == 0


def test_run_validate_returns_one_on_error(tmp_path):
    ns = _args(tmp_path, "svc:\n  - bad\n")
    assert run_validate(ns) == 1


def test_run_validate_strict_returns_one_on_warning(tmp_path):
    ns = _args(tmp_path, "svc:\n  key: null\n", strict=True)
    assert run_validate(ns) == 1


def test_run_validate_non_strict_returns_zero_on_warning(tmp_path):
    ns = _args(tmp_path, "svc:\n  key: null\n", strict=False)
    assert run_validate(ns) == 0


def test_run_validate_missing_file_returns_one(tmp_path):
    ns = argparse.Namespace(declared=str(tmp_path / "nope.yaml"), strict=False)
    assert run_validate(ns) == 1


# ---------------------------------------------------------------------------
# add_parser
# ---------------------------------------------------------------------------

def test_add_parser_registers_validate_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_parser(sub)
    ns = root.parse_args(["validate", "some_file.yaml"])
    assert ns.declared == "some_file.yaml"


def test_add_parser_strict_flag():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_parser(sub)
    ns = root.parse_args(["validate", "f.yaml", "--strict"])
    assert ns.strict is True
