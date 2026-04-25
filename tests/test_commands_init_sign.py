"""Integration tests: sign subcommand is wired into the commands registry."""
from __future__ import annotations

import argparse

from drift_watch.commands import register_all
from drift_watch.commands.sign_cmd import add_parser, run_sign


def _make_subparsers() -> argparse._SubParsersAction:  # type: ignore[type-arg]
    parser = argparse.ArgumentParser(prog="drift-watch-test")
    return parser.add_subparsers(dest="command")


def test_sign_subcommand_is_registered():
    sp = _make_subparsers()
    register_all(sp)
    parser = argparse.ArgumentParser(prog="drift-watch-test")
    sub = parser.add_subparsers(dest="command")
    register_all(sub)
    ns = parser.parse_args(["sign", "snap.json"])
    assert ns.command == "sign"


def test_sign_func_is_run_sign():
    sp = _make_subparsers()
    register_all(sp)
    parser = argparse.ArgumentParser(prog="drift-watch-test")
    sub = parser.add_subparsers(dest="command")
    register_all(sub)
    ns = parser.parse_args(["sign", "snap.json"])
    assert ns.func is run_sign


def test_sign_default_verify_is_false():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    ns = parser.parse_args(["sign", "snap.json"])
    assert ns.verify is False


def test_sign_verify_flag():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    ns = parser.parse_args(["sign", "snap.json", "--verify"])
    assert ns.verify is True


def test_sign_default_key_env():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    ns = parser.parse_args(["sign", "snap.json"])
    assert ns.key_env == "DRIFT_WATCH_SIGN_KEY"


def test_sign_custom_key_env():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_parser(sub)
    ns = parser.parse_args(["sign", "snap.json", "--key-env", "MY_SECRET"])
    assert ns.key_env == "MY_SECRET"
