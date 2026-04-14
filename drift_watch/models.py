"""Core data models for representing service configuration state."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DriftStatus(str, Enum):
    IN_SYNC = "in_sync"
    DRIFTED = "drifted"
    MISSING = "missing"
    UNKNOWN = "unknown"


@dataclass
class ConfigField:
    """Represents a single configuration key-value pair."""

    key: str
    declared_value: Any
    actual_value: Any

    @property
    def is_drifted(self) -> bool:
        return self.declared_value != self.actual_value

    def __repr__(self) -> str:
        return (
            f"ConfigField(key={self.key!r}, "
            f"declared={self.declared_value!r}, "
            f"actual={self.actual_value!r})"
        )


@dataclass
class ServiceDriftReport:
    """Aggregated drift report for a single service."""

    service_name: str
    status: DriftStatus = DriftStatus.IN_SYNC
    drifted_fields: list[ConfigField] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    extra_fields: list[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return (
            self.status != DriftStatus.IN_SYNC
            or bool(self.drifted_fields)
            or bool(self.missing_fields)
            or bool(self.extra_fields)
        )

    @property
    def total_issues(self) -> int:
        return len(self.drifted_fields) + len(self.missing_fields) + len(self.extra_fields)
