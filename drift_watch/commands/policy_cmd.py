"""policy_cmd — enforce field-level drift policies from a YAML/JSON policy file."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml


def add_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "policy",
        help="Check drift reports against a policy file and fail on violations.",
    )
    p.add_argument("policy_file", help="Path to the policy YAML/JSON file.")
    p.add_argument("snapshot", help="Snapshot file to evaluate.")
    p.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Treat warnings as errors.",
    )
    p.set_defaults(func=run_policy)


def _load_policy(path: str) -> dict[str, Any]:
    """Load a policy file (YAML or JSON)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    raw = p.read_text()
    if p.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(raw)
    else:
        data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Policy file must be a YAML/JSON mapping.")
    return data


def _evaluate_policy(
    policy: dict[str, Any], snapshot: dict[str, Any], strict: bool
) -> list[dict[str, str]]:
    """Return a list of violation dicts {service, field, level, message}."""
    violations: list[dict[str, str]] = []
    rules: list[dict[str, Any]] = policy.get("rules", [])
    for rule in rules:
        service_pattern = rule.get("service", "*")
        field = rule.get("field", "*")
        level = rule.get("level", "error")  # error | warning
        action = rule.get("action", "deny_drift")  # deny_drift | require_present

        for svc_name, svc_data in snapshot.items():
            if service_pattern != "*" and service_pattern != svc_name:
                continue
            fields: dict[str, Any] = svc_data.get("fields", {})
            if action == "deny_drift":
                for fname, fdata in fields.items():
                    if field != "*" and field != fname:
                        continue
                    if isinstance(fdata, dict) and fdata.get("drifted", False):
                        effective_level = "error" if (strict and level == "warning") else level
                        violations.append({
                            "service": svc_name,
                            "field": fname,
                            "level": effective_level,
                            "message": f"Drift detected on '{fname}' in service '{svc_name}'.",
                        })
            elif action == "require_present":
                if field != "*" and field not in fields:
                    effective_level = "error" if (strict and level == "warning") else level
                    violations.append({
                        "service": svc_name,
                        "field": field,
                        "level": effective_level,
                        "message": f"Required field '{field}' missing in service '{svc_name}'.",
                    })
    return violations


def run_policy(args) -> int:
    try:
        policy = _load_policy(args.policy_file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[policy] ERROR: {exc}", file=sys.stderr)
        return 1

    snapshot_path = Path(args.snapshot)
    if not snapshot_path.exists():
        print(f"[policy] ERROR: Snapshot not found: {args.snapshot}", file=sys.stderr)
        return 1

    try:
        snapshot: dict[str, Any] = json.loads(snapshot_path.read_text())
    except json.JSONDecodeError as exc:
        print(f"[policy] ERROR: Invalid snapshot JSON: {exc}", file=sys.stderr)
        return 1

    violations = _evaluate_policy(policy, snapshot, args.strict)

    if not violations:
        print("[policy] All checks passed. No violations found.")
        return 0

    errors = [v for v in violations if v["level"] == "error"]
    warnings = [v for v in violations if v["level"] == "warning"]

    for v in warnings:
        print(f"[policy] WARNING ({v['service']}): {v['message']}")
    for v in errors:
        print(f"[policy] ERROR ({v['service']}): {v['message']}")

    print(f"[policy] {len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0
