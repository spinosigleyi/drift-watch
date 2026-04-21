"""schema_cmd – validate live config fields against a JSON Schema."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from drift_watch.loader import ConfigLoadError, load_live_config


def add_parser(subparsers: Any) -> None:
    p = subparsers.add_parser(
        "schema",
        help="Validate live config against a JSON Schema file.",
    )
    p.add_argument("live", help="Path to live config (YAML or JSON).")
    p.add_argument("schema", help="Path to JSON Schema file.")
    p.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit 1 on warnings as well as errors.",
    )
    p.set_defaults(func=run_schema)


def _load_schema(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise ConfigLoadError(f"Schema file not found: {path}")
    except json.JSONDecodeError as exc:
        raise ConfigLoadError(f"Malformed JSON schema: {exc}")
    if not isinstance(data, dict):
        raise ConfigLoadError("Schema must be a JSON object at the top level.")
    return data


def _validate_service(service: str, fields: dict, schema: dict) -> list[dict]:
    """Return a list of issue dicts for *one* service."""
    issues: list[dict] = []
    required = schema.get("required", [])
    properties = schema.get("properties", {})

    for key in required:
        if key not in fields:
            issues.append({"service": service, "field": key, "level": "error",
                           "message": f"required field '{key}' is missing"})

    for key, value in fields.items():
        if key not in properties:
            continue
        prop = properties[key]
        expected_type = prop.get("type")
        if expected_type and not _check_type(value, expected_type):
            issues.append({"service": service, "field": key, "level": "error",
                           "message": f"field '{key}' expected type '{expected_type}'"})
        if "enum" in prop and value not in prop["enum"]:
            issues.append({"service": service, "field": key, "level": "warning",
                           "message": f"field '{key}' value {value!r} not in allowed enum"})
    return issues


_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}


def _check_type(value: Any, expected: str) -> bool:
    py_type = _TYPE_MAP.get(expected)
    if py_type is None:
        return True
    return isinstance(value, py_type)


def run_schema(args: Any) -> int:
    try:
        live = load_live_config(args.live)
        schema = _load_schema(args.schema)
    except ConfigLoadError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    all_issues: list[dict] = []
    for service, fields in live.items():
        if not isinstance(fields, dict):
            all_issues.append({"service": service, "field": "-", "level": "error",
                                "message": "service config is not a mapping"})
            continue
        all_issues.extend(_validate_service(service, fields, schema))

    errors = [i for i in all_issues if i["level"] == "error"]
    warnings = [i for i in all_issues if i["level"] == "warning"]

    for issue in all_issues:
        tag = "ERROR" if issue["level"] == "error" else "WARN "
        print(f"[{tag}] {issue['service']}: {issue['message']}")

    if not all_issues:
        print("Schema validation passed – no issues found.")

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0
