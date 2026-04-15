"""Tests for drift_watch/alerting.py."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from drift_watch.alerting import AlertPayload, build_alert_payload, dispatch_webhook
from drift_watch.models import DriftStatus, ServiceDriftReport


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _report(name: str, status: DriftStatus) -> ServiceDriftReport:
    r = ServiceDriftReport(service_name=name)
    r.status = status
    return r


# ---------------------------------------------------------------------------
# AlertPayload.to_dict
# ---------------------------------------------------------------------------

def test_alert_payload_to_dict_includes_all_keys():
    p = AlertPayload(
        drift_detected=True,
        drifted_services=["svc-a"],
        total_services=2,
        drifted_count=1,
        extra={"env": "prod"},
    )
    d = p.to_dict()
    assert d["drift_detected"] is True
    assert d["drifted_services"] == ["svc-a"]
    assert d["env"] == "prod"


# ---------------------------------------------------------------------------
# build_alert_payload
# ---------------------------------------------------------------------------

def test_build_payload_all_ok():
    reports = [_report("a", DriftStatus.OK), _report("b", DriftStatus.OK)]
    p = build_alert_payload(reports)
    assert p.drift_detected is False
    assert p.drifted_count == 0
    assert p.total_services == 2


def test_build_payload_mixed():
    reports = [
        _report("a", DriftStatus.OK),
        _report("b", DriftStatus.DRIFTED),
        _report("c", DriftStatus.MISSING),
    ]
    p = build_alert_payload(reports)
    assert p.drift_detected is True
    assert set(p.drifted_services) == {"b", "c"}
    assert p.drifted_count == 2


def test_build_payload_passes_extra():
    p = build_alert_payload([], extra={"source": "ci"})
    assert p.extra["source"] == "ci"


# ---------------------------------------------------------------------------
# dispatch_webhook
# ---------------------------------------------------------------------------

def _mock_response(status: int = 200):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_dispatch_webhook_success():
    payload = AlertPayload(drift_detected=False, total_services=1)
    with patch("urllib.request.urlopen", return_value=_mock_response(200)):
        ok, msg = dispatch_webhook("http://example.com/hook", payload)
    assert ok is True
    assert "200" in msg


def test_dispatch_webhook_http_error():
    import urllib.error
    payload = AlertPayload(drift_detected=True, drifted_services=["x"], drifted_count=1)
    err = urllib.error.HTTPError(url=None, code=500, msg="Server Error", hdrs=None, fp=None)
    with patch("urllib.request.urlopen", side_effect=err):
        ok, msg = dispatch_webhook("http://example.com/hook", payload)
    assert ok is False
    assert "500" in msg


def test_dispatch_webhook_url_error():
    import urllib.error
    payload = AlertPayload(drift_detected=False)
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        ok, msg = dispatch_webhook("http://bad/hook", payload)
    assert ok is False
    assert "timeout" in msg


def test_dispatch_webhook_sends_json_body():
    captured = {}

    def fake_urlopen(req, timeout):
        captured["data"] = json.loads(req.data.decode())
        return _mock_response()

    payload = AlertPayload(drift_detected=True, drifted_services=["svc"], drifted_count=1, total_services=1)
    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        dispatch_webhook("http://example.com/hook", payload)

    assert captured["data"]["drift_detected"] is True
    assert "svc" in captured["data"]["drifted_services"]
