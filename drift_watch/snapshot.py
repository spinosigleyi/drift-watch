"""Snapshot management for drift-watch.

Allows saving and loading configuration snapshots so drift can be
detected against a previously captured baseline rather than a live
environment.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

SNAPSHOT_VERSION = 1


class SnapshotError(Exception):
    """Raised when a snapshot cannot be saved or loaded."""


def save_snapshot(config: Dict[str, Any], path: str | os.PathLike) -> None:
    """Persist *config* as a JSON snapshot file at *path*.

    Args:
        config: Mapping of service name -> field dict to snapshot.
        path:   Destination file path (will be created/overwritten).

    Raises:
        SnapshotError: If the file cannot be written.
    """
    payload = {
        "version": SNAPSHOT_VERSION,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "services": config,
    }
    try:
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        raise SnapshotError(f"Could not write snapshot to {path!r}: {exc}") from exc


def load_snapshot(path: str | os.PathLike) -> Dict[str, Any]:
    """Load a previously saved snapshot from *path*.

    Returns:
        The ``services`` mapping stored in the snapshot.

    Raises:
        SnapshotError: If the file is missing, unreadable, or malformed.
    """
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SnapshotError(f"Snapshot file not found: {path!r}") from exc
    except OSError as exc:
        raise SnapshotError(f"Could not read snapshot {path!r}: {exc}") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"Snapshot {path!r} is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict) or "services" not in payload:
        raise SnapshotError(
            f"Snapshot {path!r} is missing required 'services' key."
        )

    services = payload["services"]
    if not isinstance(services, dict):
        raise SnapshotError(
            f"Snapshot {path!r}: 'services' must be a mapping, got {type(services).__name__}."
        )
    return services
