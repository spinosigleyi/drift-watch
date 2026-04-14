"""Unit tests for the drift detection module."""

import pytest

from drift_watch.detector import detect_drift
from drift_watch.models import DriftStatus


DECLARED = {
    "image": "nginx:1.25",
    "replicas": 3,
    "memory_limit": "512Mi",
    "env": "production",
}


def test_no_drift_when_configs_match():
    report = detect_drift("web", DECLARED, DECLARED.copy())
    assert report.status == DriftStatus.IN_SYNC
    assert not report.has_drift
    assert report.total_issues == 0


def test_detects_value_drift():
    actual = {**DECLARED, "replicas": 1, "image": "nginx:1.24"}
    report = detect_drift("web", DECLARED, actual)
    assert report.status == DriftStatus.DRIFTED
    drifted_keys = {f.key for f in report.drifted_fields}
    assert drifted_keys == {"replicas", "image"}


def test_detects_missing_fields():
    actual = {k: v for k, v in DECLARED.items() if k != "memory_limit"}
    report = detect_drift("web", DECLARED, actual)
    assert report.status == DriftStatus.DRIFTED
    assert "memory_limit" in report.missing_fields


def test_detects_extra_fields():
    actual = {**DECLARED, "cpu_limit": "250m"}
    report = detect_drift("web", DECLARED, actual)
    assert report.status == DriftStatus.DRIFTED
    assert "cpu_limit" in report.extra_fields


def test_missing_service_returns_missing_status():
    report = detect_drift("ghost-service", DECLARED, None)
    assert report.status == DriftStatus.MISSING
    assert report.service_name == "ghost-service"


def test_config_field_is_drifted_property():
    from drift_watch.models import ConfigField

    f = ConfigField(key="replicas", declared_value=3, actual_value=1)
    assert f.is_drifted is True

    f_same = ConfigField(key="env", declared_value="production", actual_value="production")
    assert f_same.is_drifted is False


def test_total_issues_counts_all_drift_types():
    actual = {"image": "nginx:1.24", "cpu_limit": "250m"}  # missing replicas, memory_limit, env
    report = detect_drift("web", DECLARED, actual)
    assert report.total_issues == len(report.drifted_fields) + len(report.missing_fields) + len(report.extra_fields)
