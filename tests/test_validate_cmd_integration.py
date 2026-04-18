"""Integration tests: validate_cmd wired through commands/__init__.py"""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from drift_watch.commands import register_all


def _build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="drift-watch")
    sub = root.add_subparsers(dest="command")
    register_all(sub)
    return root


def test_validate_subcommand_registered():
    parser = _build_parser()
    ns = parser.parse_args(["validate", "declared.yaml"])
    assert ns.command == "validate"


def test_validate_func_is_run_validate():
    from drift_watch.commands.validate_cmd import run_validate
    parser = _build_parser()
    ns = parser.parse_args(["validate", "declared.yaml"])
    assert ns.func is run_validate


def test_validate_end_to_end_clean(tmp_path: Path):
    declared = tmp_path / "declared.yaml"
    declared.write_text("api:\n  port: 3000\n  replicas: 2\n")
    parser = _build_parser()
    ns = parser.parse_args(["validate", str(declared)])
    assert ns.func(ns) == 0


def test_validate_end_to_end_strict_null(tmp_path: Path):
    declared = tmp_path / "declared.yaml"
    declared.write_text("api:\n  port: null\n")
    parser = _build_parser()
    ns = parser.parse_args(["validate", str(declared), "--strict"])
    assert ns.func(ns) == 1
