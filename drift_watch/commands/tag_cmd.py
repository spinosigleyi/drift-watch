"""tag_cmd — attach arbitrary key=value tags to a snapshot file."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("tag", help="attach tags to a snapshot")
    p.add_argument("snapshot", help="path to snapshot JSON file")
    p.add_argument(
        "tags",
        nargs="+",
        metavar="KEY=VALUE",
        help="tags to attach, e.g. env=prod team=platform",
    )
    p.set_defaults(func=run_tag)


def _parse_tags(raw: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"tag must be KEY=VALUE, got: {item!r}")
        k, v = item.split("=", 1)
        k = k.strip()
        if not k:
            raise ValueError(f"tag key must not be empty, got: {item!r}")
        result[k] = v.strip()
    return result


def run_tag(args: argparse.Namespace) -> int:
    path = Path(args.snapshot)
    if not path.exists():
        print(f"[error] snapshot not found: {path}")
        return 1

    try:
        data: dict = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[error] could not read snapshot: {exc}")
        return 1

    try:
        new_tags = _parse_tags(args.tags)
    except ValueError as exc:
        print(f"[error] {exc}")
        return 1

    existing: dict[str, str] = data.get("tags", {})
    existing.update(new_tags)
    data["tags"] = existing

    try:
        path.write_text(json.dumps(data, indent=2))
    except OSError as exc:
        print(f"[error] could not write snapshot: {exc}")
        return 1

    print(f"Tagged {path.name} with {new_tags}")
    return 0
