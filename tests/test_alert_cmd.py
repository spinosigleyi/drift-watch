"""Tests for drift_watch/commands/alert_cmd.py."""
from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from drift_watch.commands.alert_cmd import _build_payload, _post_payload, run_alert
from drift_watch.models import DriftStatus, ServiceDriftReport


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_report(name: str, status: DriftStatus) -> ServiceDriftReport:
    r = ServiceDriftReport(service_name=name)
    r.status = status
    return r


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "declared": "declared.yaml",
        "live": "live.yaml",
        "webhook": "http://example.com/hook",
        "only_drifted": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# _build_payload
# ---------------------------------------------------------------------------

def test_build_payload_no_drift():
    reports = [_make_report("svc-a", DriftStatus.OK)]
    p = _build_payload(reports)
    assert p["drift_detected"] is False
    assert p["drifted_services"] == []
    assert p["total_services"] == 1


def test_build_payload_with_drift():
    reports = [
        _make_report("svc-a", DriftStatus.OK),
        _make_report("svc-b", DriftStatus.DRIFTED),
        _make_report("svc-c", DriftStatus.MISSING),
    ]
    p = _build_payload(reports)
    assert p["drift_detected"] is True
    assert set(p["drifted_services"]) == {"svc-b", "svc-c"}
    assert p["drifted_count"] == 2


# ---------------------------------------------------------------------------
# _post_payload
# ---------------------------------------------------------------------------

def test_post_payload_returns_true_on_success():
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _post_payload("http://example.com/hook", {"key": "val"})
    assert result is True


def test_post_payload_returns_false_on_error():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        result = _post_payload("http://bad-host/hook", {})
    assert result is False


# ---------------------------------------------------------------------------
# run_alert
# ---------------------------------------------------------------------------

def test_run_alert_returns_1_on_load_error():
    from drift_watch.loader import ConfigLoadError
    with patch("drift_watch.commands.alert_cmd.load_declared_config",
               side_effect=ConfigLoadError("bad file")):
        assert run_alert(_args()) == 1


def test_run_alert_skips_webhook_when_only_drifted_and_no_drift(capsys):
    ok_reports = [_make_report("svc-a", DriftStatus.OK)]
    with patch("drift_watch.commands.alert_cmd.load_declared_config", return_value={}):
        with patch("drift_watch.commands.alert_cmd.load_live_config", return_value={}):
            with patch("drift_watch.commands.alert_cmd.detect_drift", return_value=ok_reports):
                result = run_alert(_args(only_drifted=True))
    assert result == 0
    assert "skipping" in capsys.readouterr().out


def test_run_alert_returns_1_when_webhook_fails():
    drifted = [_make_report("svc-b", DriftStatus.DRIFTED)]
    with patch("drift_watch.commands.alert_cmd.load_declared_config", return_value={}):
        with patch("drift_watch.commands.alert_cmd.load_live_config", return_value={}):
            with patch("drift_watch.commands.alert_cmd.detect_drift", return_value=drifted):
                with patch("drift_watch.commands.alert_cmd._post_payload", return_value=False):
                    assert run_alert(_args()) == 1


def test_run_alert_returns_0_on_success(capsys):
    ok_reports = [_make_report("svc-a", DriftStatus.OK)]
    with patch("drift_watch.commands.alert_cmd.load_declared_config", return_value={}):
        with patch("drift_watch.commands.alert_cmd.load_live_config", return_value={}):
            with patch("drift_watch.commands.alert_cmd.detect_drift", return_value=ok_reports):
                with patch("drift_watch.commands.alert_cmd._post_payload", return_value=True):
                    result = run_alert(_args())
    assert result == 0
    assert "sent" in capsys.readouterr().out
