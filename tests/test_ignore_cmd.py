"""Tests for drift_watch/commands/ignore_cmd.py."""
from __future__ import annotations

import json
import os
import types

import pytest

from drift_watch.commands.ignore_cmd import (
    DEFAULT_IGNORE_FILE,
    _load,
    _save,
    is_ignored,
    run_ignore,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _args(tmp_path, action, pattern=None):
    ns = types.SimpleNamespace(
        file=str(tmp_path / ".driftignore"),
        ignore_action=action,
        pattern=pattern,
    )
    return ns


# ---------------------------------------------------------------------------
# _load / _save
# ---------------------------------------------------------------------------

def test_load_returns_empty_for_missing_file(tmp_path):
    assert _load(str(tmp_path / "nofile.json")) == []


def test_save_and_load_roundtrip(tmp_path):
    path = str(tmp_path / ".driftignore")
    _save(path, ["env.*", "debug"])
    loaded = _load(path)
    assert sorted(loaded) == ["debug", "env.*"]


def test_save_deduplicates(tmp_path):
    path = str(tmp_path / ".driftignore")
    _save(path, ["a", "a", "b"])
    assert _load(path).count("a") == 1


def test_load_raises_on_non_array(tmp_path):
    path = str(tmp_path / ".driftignore")
    path_obj = tmp_path / ".driftignore"
    path_obj.write_text(json.dumps({"key": "value"}))
    with pytest.raises(ValueError, match="must contain a JSON array"):
        _load(path)


# ---------------------------------------------------------------------------
# is_ignored
# ---------------------------------------------------------------------------

def test_is_ignored_exact_match():
    assert is_ignored("debug", ["debug"])


def test_is_ignored_glob_match():
    assert is_ignored("env.SECRET", ["env.*"])


def test_is_ignored_no_match():
    assert not is_ignored("replicas", ["env.*", "debug"])


def test_is_ignored_empty_patterns():
    assert not is_ignored("anything", [])


# ---------------------------------------------------------------------------
# run_ignore – list
# ---------------------------------------------------------------------------

def test_list_empty(tmp_path, capsys):
    assert run_ignore(_args(tmp_path, "list")) == 0
    out = capsys.readouterr().out
    assert "no patterns" in out


def test_list_shows_patterns(tmp_path, capsys):
    path = str(tmp_path / ".driftignore")
    _save(path, ["env.*", "debug"])
    assert run_ignore(_args(tmp_path, "list")) == 0
    out = capsys.readouterr().out
    assert "env.*" in out
    assert "debug" in out


# ---------------------------------------------------------------------------
# run_ignore – add
# ---------------------------------------------------------------------------

def test_add_creates_file(tmp_path):
    run_ignore(_args(tmp_path, "add", pattern="env.*"))
    path = str(tmp_path / ".driftignore")
    assert "env.*" in _load(path)


def test_add_duplicate_is_idempotent(tmp_path, capsys):
    run_ignore(_args(tmp_path, "add", pattern="debug"))
    rc = run_ignore(_args(tmp_path, "add", pattern="debug"))
    assert rc == 0
    assert capsys.readouterr().out.strip().endswith("already present: debug")


# ---------------------------------------------------------------------------
# run_ignore – remove
# ---------------------------------------------------------------------------

def test_remove_existing_pattern(tmp_path):
    run_ignore(_args(tmp_path, "add", pattern="env.*"))
    rc = run_ignore(_args(tmp_path, "remove", pattern="env.*"))
    assert rc == 0
    assert "env.*" not in _load(str(tmp_path / ".driftignore"))


def test_remove_missing_pattern_returns_1(tmp_path):
    rc = run_ignore(_args(tmp_path, "remove", pattern="nonexistent"))
    assert rc == 1
