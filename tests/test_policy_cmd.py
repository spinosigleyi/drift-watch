"""Tests for drift_watch/commands/policy_cmd.py."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from drift_watch.commands.policy_cmd import (
    _evaluate_policy,
    _load_policy,
    run_policy,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _args(policy_file: str, snapshot: str, strict: bool = False) -> SimpleNamespace:
    return SimpleNamespace(policy_file=policy_file, snapshot=snapshot, strict=strict)


def _write_yaml(path: Path, data) -> None:
    path.write_text(yaml.dump(data))


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# _load_policy
# ---------------------------------------------------------------------------

def test_load_policy_yaml(tmp_path):
    p = tmp_path / "policy.yaml"
    _write_yaml(p, {"rules": []})
    result = _load_policy(str(p))
    assert result == {"rules": []}


def test_load_policy_json(tmp_path):
    p = tmp_path / "policy.json"
    _write_json(p, {"rules": [{"service": "*", "field": "*", "action": "deny_drift"}]})
    result = _load_policy(str(p))
    assert len(result["rules"]) == 1


def test_load_policy_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        _load_policy(str(tmp_path / "nope.yaml"))


def test_load_policy_non_mapping_raises(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("- item1\n- item2\n")
    with pytest.raises(ValueError, match="mapping"):
        _load_policy(str(p))


# ---------------------------------------------------------------------------
# _evaluate_policy
# ---------------------------------------------------------------------------

def _drifted_snapshot():
    return {
        "svc-a": {
            "fields": {
                "image": {"declared": "v1", "live": "v2", "drifted": True},
                "replicas": {"declared": 2, "live": 2, "drifted": False},
            }
        }
    }


def test_evaluate_deny_drift_catches_drifted_field():
    policy = {"rules": [{"service": "*", "field": "*", "action": "deny_drift", "level": "error"}]}
    violations = _evaluate_policy(policy, _drifted_snapshot(), strict=False)
    assert len(violations) == 1
    assert violations[0]["field"] == "image"
    assert violations[0]["level"] == "error"


def test_evaluate_deny_drift_specific_field_no_match():
    policy = {"rules": [{"service": "*", "field": "replicas", "action": "deny_drift", "level": "error"}]}
    violations = _evaluate_policy(policy, _drifted_snapshot(), strict=False)
    assert violations == []


def test_evaluate_require_present_missing_field():
    policy = {"rules": [{"service": "svc-a", "field": "memory", "action": "require_present", "level": "warning"}]}
    violations = _evaluate_policy(policy, _drifted_snapshot(), strict=False)
    assert len(violations) == 1
    assert violations[0]["level"] == "warning"


def test_evaluate_strict_upgrades_warning_to_error():
    policy = {"rules": [{"service": "*", "field": "image", "action": "deny_drift", "level": "warning"}]}
    violations = _evaluate_policy(policy, _drifted_snapshot(), strict=True)
    assert violations[0]["level"] == "error"


def test_evaluate_service_pattern_filters():
    policy = {"rules": [{"service": "svc-b", "field": "*", "action": "deny_drift", "level": "error"}]}
    violations = _evaluate_policy(policy, _drifted_snapshot(), strict=False)
    assert violations == []


# ---------------------------------------------------------------------------
# run_policy integration
# ---------------------------------------------------------------------------

def test_run_policy_no_violations_returns_zero(tmp_path):
    policy_path = tmp_path / "policy.yaml"
    _write_yaml(policy_path, {"rules": []})
    snap_path = tmp_path / "snap.json"
    _write_json(snap_path, {"svc-a": {"fields": {}}})
    assert run_policy(_args(str(policy_path), str(snap_path))) == 0


def test_run_policy_errors_return_one(tmp_path):
    policy_path = tmp_path / "policy.yaml"
    _write_yaml(policy_path, {"rules": [{"service": "*", "field": "*", "action": "deny_drift", "level": "error"}]})
    snap_path = tmp_path / "snap.json"
    _write_json(snap_path, _drifted_snapshot())
    assert run_policy(_args(str(policy_path), str(snap_path))) == 1


def test_run_policy_missing_policy_returns_one(tmp_path):
    snap_path = tmp_path / "snap.json"
    _write_json(snap_path, {})
    assert run_policy(_args(str(tmp_path / "nope.yaml"), str(snap_path))) == 1


def test_run_policy_missing_snapshot_returns_one(tmp_path):
    policy_path = tmp_path / "policy.yaml"
    _write_yaml(policy_path, {"rules": []})
    assert run_policy(_args(str(policy_path), str(tmp_path / "nope.json"))) == 1


def test_run_policy_warnings_only_returns_zero(tmp_path):
    policy_path = tmp_path / "policy.yaml"
    _write_yaml(policy_path, {"rules": [{"service": "*", "field": "*", "action": "deny_drift", "level": "warning"}]})
    snap_path = tmp_path / "snap.json"
    _write_json(snap_path, _drifted_snapshot())
    assert run_policy(_args(str(policy_path), str(snap_path), strict=False)) == 0
