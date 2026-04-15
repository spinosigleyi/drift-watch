"""alerting — low-level helpers for constructing and dispatching drift alerts.

This module is intentionally decoupled from CLI concerns so it can be
reused programmatically (e.g. from a scheduler or Lambda handler).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Sequence

from drift_watch.models import DriftStatus, ServiceDriftReport


@dataclass
class AlertPayload:
    drift_detected: bool
    drifted_services: list[str] = field(default_factory=list)
    total_services: int = 0
    drifted_count: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "drift_detected": self.drift_detected,
            "drifted_services": self.drifted_services,
            "total_services": self.total_services,
            "drifted_count": self.drifted_count,
            **self.extra,
        }


_DRIFTED_STATUSES = frozenset({DriftStatus.DRIFTED, DriftStatus.MISSING})


def build_alert_payload(
    reports: Sequence[ServiceDriftReport],
    extra: dict[str, Any] | None = None,
) -> AlertPayload:
    """Build an :class:`AlertPayload` from a list of drift reports."""
    drifted = [r.service_name for r in reports if r.status in _DRIFTED_STATUSES]
    return AlertPayload(
        drift_detected=len(drifted) > 0,
        drifted_services=drifted,
        total_services=len(reports),
        drifted_count=len(drifted),
        extra=extra or {},
    )


def dispatch_webhook(
    url: str,
    payload: AlertPayload,
    *,
    timeout: int = 10,
    extra_headers: dict[str, str] | None = None,
) -> tuple[bool, str]:
    """POST *payload* as JSON to *url*.

    Returns ``(success, message)``.
    """
    headers = {"Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)

    data = json.dumps(payload.to_dict()).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP error {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        return False, f"URL error: {exc.reason}"
