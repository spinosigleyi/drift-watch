"""Loaders for declared (IaC) and live service configurations."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

import yaml


class ConfigLoadError(Exception):
    """Raised when a configuration file cannot be loaded or parsed."""


def load_declared_config(path: str) -> Dict[str, Dict[str, Any]]:
    """Load declared service configurations from a YAML or JSON file.

    The file is expected to be a mapping of service names to their
    configuration key/value pairs, e.g.:

        my-service:
          replicas: 3
          image: myapp:1.2.0
          env: production

    Args:
        path: Filesystem path to the YAML or JSON config file.

    Returns:
        A dict mapping service name -> config dict.

    Raises:
        ConfigLoadError: If the file is missing, unreadable, or malformed.
    """
    if not os.path.exists(path):
        raise ConfigLoadError(f"Declared config file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        raise ConfigLoadError(f"Cannot read file {path}: {exc}") from exc

    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in (".yaml", ".yml"):
            data = yaml.safe_load(raw)
        elif ext == ".json":
            data = json.loads(raw)
        else:
            # Try YAML as a fallback (YAML is a superset of JSON)
            data = yaml.safe_load(raw)
    except Exception as exc:
        raise ConfigLoadError(f"Failed to parse {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigLoadError(
            f"Expected a mapping at the top level of {path}, got {type(data).__name__}"
        )

    return {str(k): dict(v) for k, v in data.items()}


def load_live_config(service_name: str, source: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Retrieve the live configuration for a single service.

    In a real implementation this would query an API (e.g. Kubernetes,
    AWS ECS, Consul).  Here we accept a pre-fetched *source* mapping so
    that the function is easy to test and mock.

    Args:
        service_name: The name of the service to look up.
        source: A mapping of service name -> live config dict.

    Returns:
        The live config dict, or an empty dict if the service is absent.
    """
    return dict(source.get(service_name, {}))
