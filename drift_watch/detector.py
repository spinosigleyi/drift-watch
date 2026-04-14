"""Drift detection logic comparing declared vs actual service configuration."""

from typing import Any

from drift_watch.models import ConfigField, DriftStatus, ServiceDriftReport


def detect_drift(
    service_name: str,
    declared: dict[str, Any],
    actual: dict[str, Any],
) -> ServiceDriftReport:
    """
    Compare declared IaC configuration against the actual deployed state.

    Args:
        service_name: Identifier for the service being checked.
        declared: Configuration as defined in infrastructure-as-code.
        actual: Configuration as observed from the live deployment.

    Returns:
        A ServiceDriftReport summarising any detected drift.
    """
    report = ServiceDriftReport(service_name=service_name)

    if actual is None:
        report.status = DriftStatus.MISSING
        return report

    declared_keys = set(declared.keys())
    actual_keys = set(actual.keys())

    # Fields present in declared but absent in actual deployment
    report.missing_fields = sorted(declared_keys - actual_keys)

    # Fields present in actual but not declared (unexpected additions)
    report.extra_fields = sorted(actual_keys - declared_keys)

    # Fields present in both — check for value mismatches
    for key in declared_keys & actual_keys:
        if declared[key] != actual[key]:
            report.drifted_fields.append(
                ConfigField(
                    key=key,
                    declared_value=declared[key],
                    actual_value=actual[key],
                )
            )

    report.drifted_fields.sort(key=lambda f: f.key)

    if report.has_drift:
        report.status = DriftStatus.DRIFTED

    return report
