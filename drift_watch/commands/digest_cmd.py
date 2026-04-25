"""digest_cmd – produce a short fingerprint/digest for a snapshot file.

The digest is a SHA-256 hash of the canonical (sorted-key) JSON
representation of the snapshot, making it easy to tell at a glance
whether two snapshots are byte-for-byte equivalent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from drift_watch.snapshot import load_snapshot, SnapshotError


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "digest",
        help="Print a SHA-256 fingerprint of a snapshot file.",
    )
    p.add_argument(
        "snapshot",
        help="Path to the snapshot JSON file.",
    )
    p.add_argument(
        "--short",
        action="store_true",
        default=False,
        help="Print only the first 12 characters of the digest.",
    )
    p.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        default=False,
        help="Emit result as JSON.",
    )
    p.set_defaults(func=run_digest)


def _compute_digest(snapshot_path: Path) -> str:
    """Return the hex SHA-256 of the canonical JSON for *snapshot_path*."""
    raw = snapshot_path.read_text(encoding="utf-8")
    data = json.loads(raw)
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def run_digest(args: argparse.Namespace) -> int:
    path = Path(args.snapshot)

    if not path.exists():
        print(f"[digest] error: file not found: {path}")
        return 1

    try:
        # Validate it is a parseable snapshot before hashing.
        load_snapshot(path)
    except SnapshotError as exc:
        print(f"[digest] error: {exc}")
        return 1

    try:
        digest = _compute_digest(path)
    except Exception as exc:  # pragma: no cover
        print(f"[digest] error: {exc}")
        return 1

    display = digest[:12] if args.short else digest

    if args.json_output:
        import sys
        json.dump({"path": str(path), "digest": display, "short": args.short}, sys.stdout)
        print()
    else:
        print(f"{display}  {path}")

    return 0
