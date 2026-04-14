"""Tests for drift_watch.reporter output formatting."""

from __future__ import annotations

import io
import json

import pytest

from drift_watch.models import ConfigField, DriftStatus, ServiceDriftReport
from drift_watch.reporter import format_json_report, format_text_report


def _make_report(name, status, fields=None):
    return ServiceDriftReport(
        service_name=name,
        status=status,
        drifted_fields=fields or [],
    )


def test_text_report_ok_service():
    report = _make_report("api", DriftStatus.OK)
    out = io.StringIO()
    format_text_report([report], use_color=False, out=out)
    text = out.getvalue()
    assert "api" in text
    assert "ok" in text.lower()
    assert "All fields match" in text


def test_text_report_drifted_service():
    field = ConfigField(key="replicas", expected=3, actual=1)
    report = _make_report("worker", DriftStatus.DRIFTED, [field])
    out = io.StringIO()
    format_text_report([report], use_color=False, out=out)
    text = out.getvalue()
    assert "worker" in text
    assert "replicas" in text
    assert "expected=3" in text
    assert "actual=1" in text


def test_text_report_missing_service():
    report = _make_report("ghost", DriftStatus.MISSING)
    out = io.StringIO()
    format_text_report([report], use_color=False, out=out)
    text = out.getvalue()
    assert "ghost" in text
    assert "not found" in text.lower()


def test_text_report_summary_counts():
    reports = [
        _make_report("a", DriftStatus.OK),
        _make_report("b", DriftStatus.DRIFTED, [ConfigField("x", 1, 2)]),
        _make_report("c", DriftStatus.MISSING),
    ]
    out = io.StringIO()
    format_text_report(reports, use_color=False, out=out)
    text = out.getvalue()
    assert "3 service(s) checked" in text
    assert "1 drifted" in text
    assert "1 missing" in text


def test_json_report_structure():
    field = ConfigField(key="image", expected="v1", actual="v2")
    reports = [
        _make_report("svc", DriftStatus.DRIFTED, [field]),
    ]
    result = json.loads(format_json_report(reports))
    assert len(result) == 1
    entry = result[0]
    assert entry["service"] == "svc"
    assert entry["status"] == "drifted"
    assert entry["drifted_fields"][0]["key"] == "image"
    assert entry["drifted_fields"][0]["expected"] == "v1"
    assert entry["drifted_fields"][0]["actual"] == "v2"


def test_json_report_empty():
    result = json.loads(format_json_report([]))
    assert result == []
