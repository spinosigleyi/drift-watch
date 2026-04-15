"""Tests for drift_watch/commands/watch_cmd.py."""
from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from drift_watch.commands.watch_cmd import add_parser, run_watch, _run_once


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def declared_file(tmp_path: Path) -> Path:
    f = tmp_path / "declared.yaml"
    f.write_text(textwrap.dedent("""\
        web:
          replicas: 3
          image: nginx:1.25
    """))
    return f


@pytest.fixture()
def live_matching_file(tmp_path: Path) -> Path:
    f = tmp_path / "live.json"
    f.write_text(json.dumps({"web": {"replicas": 3, "image": "nginx:1.25"}}))
    return f


@pytest.fixture()
def live_drifted_file(tmp_path: Path) -> Path:
    f = tmp_path / "live_drifted.json"
    f.write_text(json.dumps({"web": {"replicas": 5, "image": "nginx:1.25"}}))
    return f


def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(declared="declared.yaml", live="live.json",
                    interval=60, webhook=None, once=True)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# add_parser
# ---------------------------------------------------------------------------

def test_add_parser_registers_watch_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_parser(sub)
    args = root.parse_args(["watch", "d.yaml", "l.json", "--once"])
    assert args.once is True


def test_add_parser_defaults():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_parser(sub)
    args = root.parse_args(["watch", "d.yaml", "l.json"])
    assert args.interval == 60
    assert args.webhook is None
    assert args.once is False


# ---------------------------------------------------------------------------
# _run_once
# ---------------------------------------------------------------------------

def test_run_once_no_drift(declared_file, live_matching_file):
    drifted = _run_once(str(declared_file), str(live_matching_file), webhook=None)
    assert drifted is False


def test_run_once_detects_drift(declared_file, live_drifted_file):
    drifted = _run_once(str(declared_file), str(live_drifted_file), webhook=None)
    assert drifted is True


def test_run_once_load_error_returns_false(tmp_path):
    drifted = _run_once("nonexistent.yaml", "nonexistent.json", webhook=None)
    assert drifted is False


def test_run_once_calls_webhook_on_drift(declared_file, live_drifted_file):
    with patch("drift_watch.commands.watch_cmd.dispatch_webhook", return_value=True) as mock_dw:
        _run_once(str(declared_file), str(live_drifted_file), webhook="http://hook.example.com")
    mock_dw.assert_called_once()


def test_run_once_no_webhook_call_when_no_drift(declared_file, live_matching_file):
    with patch("drift_watch.commands.watch_cmd.dispatch_webhook") as mock_dw:
        _run_once(str(declared_file), str(live_matching_file), webhook="http://hook.example.com")
    mock_dw.assert_not_called()


# ---------------------------------------------------------------------------
# run_watch
# ---------------------------------------------------------------------------

def test_run_watch_once_returns_zero(declared_file, live_matching_file):
    args = _args(declared=str(declared_file), live=str(live_matching_file), once=True)
    assert run_watch(args) == 0


def test_run_watch_keyboard_interrupt_returns_zero(declared_file, live_matching_file):
    with patch("drift_watch.commands.watch_cmd._run_once", side_effect=KeyboardInterrupt):
        args = _args(declared=str(declared_file), live=str(live_matching_file), once=False)
        assert run_watch(args) == 0
