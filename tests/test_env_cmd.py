"""Tests for drift_watch/commands/env_cmd.py."""
from __future__ import annotations

import argparse
import json
import os
import textwrap
from pathlib import Path

import pytest

from drift_watch.commands.env_cmd import add_parser, _env_snapshot, run_env


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _args(
    declared: str,
    prefix: str = "",
    exit_on_drift: bool = False,
) -> argparse.Namespace:
    ns = argparse.Namespace()
    ns.declared = declared
    ns.prefix = prefix
    ns.exit_on_drift = exit_on_drift
    return ns


@pytest.fixture()
def declared_file(tmp_path: Path) -> Path:
    cfg = tmp_path / "declared.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            web:
              HOST: localhost
              PORT: "8080"
            """
        )
    )
    return cfg


# ---------------------------------------------------------------------------
# _env_snapshot
# ---------------------------------------------------------------------------


def test_env_snapshot_no_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOO", "bar")
    monkeypatch.setenv("BAZ", "qux")
    snap = _env_snapshot("")
    assert snap["FOO"] == "bar"
    assert snap["BAZ"] == "qux"


def test_env_snapshot_with_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_HOST", "example.com")
    monkeypatch.setenv("OTHER_KEY", "ignored")
    snap = _env_snapshot("APP_")
    assert "APP_HOST" in snap
    assert "OTHER_KEY" not in snap


# ---------------------------------------------------------------------------
# run_env
# ---------------------------------------------------------------------------


def test_run_env_no_drift_exits_zero(
    declared_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOST", "localhost")
    monkeypatch.setenv("PORT", "8080")
    rc = run_env(_args(str(declared_file)))
    assert rc == 0


def test_run_env_drift_without_flag_exits_zero(
    declared_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOST", "wrong-host")
    monkeypatch.setenv("PORT", "9999")
    rc = run_env(_args(str(declared_file), exit_on_drift=False))
    assert rc == 0


def test_run_env_drift_with_flag_exits_one(
    declared_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOST", "wrong-host")
    monkeypatch.delenv("PORT", raising=False)
    rc = run_env(_args(str(declared_file), exit_on_drift=True))
    assert rc == 1


def test_run_env_bad_declared_returns_1(tmp_path: Path) -> None:
    rc = run_env(_args(str(tmp_path / "missing.yaml")))
    assert rc == 1


def test_run_env_prefix_filters_env(
    declared_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # With prefix="APP_" none of the declared keys (HOST, PORT) will be found,
    # so live values are None → drift expected.
    monkeypatch.setenv("APP_HOST", "localhost")
    rc = run_env(_args(str(declared_file), prefix="APP_", exit_on_drift=True))
    assert rc == 1


# ---------------------------------------------------------------------------
# add_parser
# ---------------------------------------------------------------------------


def test_add_parser_registers_env_subcommand() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    ns = parser.parse_args(["env", "declared.yaml"])
    assert ns.func is run_env


def test_add_parser_default_exit_on_drift_is_false() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    ns = parser.parse_args(["env", "declared.yaml"])
    assert ns.exit_on_drift is False


def test_add_parser_default_prefix_is_empty() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    ns = parser.parse_args(["env", "declared.yaml"])
    assert ns.prefix == ""
