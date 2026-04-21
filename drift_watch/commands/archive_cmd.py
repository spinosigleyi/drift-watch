"""archive_cmd – compress old snapshots into a .tar.gz archive."""
from __future__ import annotations

import argparse
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SNAPSHOT_DIR = "snapshots"
DEFAULT_ARCHIVE_DIR = "archives"


def add_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "archive",
        help="Compress snapshots older than N days into a tar.gz archive.",
    )
    p.add_argument(
        "--snapshot-dir",
        default=DEFAULT_SNAPSHOT_DIR,
        help="Directory containing snapshot JSON files (default: snapshots).",
    )
    p.add_argument(
        "--archive-dir",
        default=DEFAULT_ARCHIVE_DIR,
        help="Directory where the archive will be written (default: archives).",
    )
    p.add_argument(
        "--older-than",
        type=int,
        default=30,
        metavar="DAYS",
        help="Archive snapshots older than this many days (default: 30).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print files that would be archived without doing anything.",
    )
    p.set_defaults(func=run_archive)


def _snapshot_timestamp(path: Path) -> datetime | None:
    """Return the 'timestamp' field from a snapshot file, or None."""
    try:
        data = json.loads(path.read_text())
        ts = data.get("timestamp")
        if ts:
            return datetime.fromisoformat(ts)
    except Exception:  # noqa: BLE001
        return None
    return None


def _collect_old_snapshots(snapshot_dir: Path, older_than_days: int) -> list[Path]:
    """Return snapshot paths whose timestamp is older than *older_than_days*."""
    if not snapshot_dir.is_dir():
        return []
    cutoff = datetime.now(tz=timezone.utc).replace(tzinfo=None) if True else None
    from datetime import timedelta
    cutoff = datetime.now(tz=timezone.utc).replace(tzinfo=None) - timedelta(days=older_than_days)  # noqa: E501
    old: list[Path] = []
    for p in sorted(snapshot_dir.glob("*.json")):
        ts = _snapshot_timestamp(p)
        if ts is not None and ts.replace(tzinfo=None) < cutoff:
            old.append(p)
    return old


def run_archive(args: argparse.Namespace) -> int:
    snapshot_dir = Path(args.snapshot_dir)
    archive_dir = Path(args.archive_dir)
    older_than: int = args.older_than
    dry_run: bool = args.dry_run

    candidates = _collect_old_snapshots(snapshot_dir, older_than)
    if not candidates:
        print("No snapshots old enough to archive.")
        return 0

    if dry_run:
        print(f"Would archive {len(candidates)} snapshot(s):")
        for p in candidates:
            print(f"  {p}")
        return 0

    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_path = archive_dir / f"snapshots_{stamp}.tar.gz"

    with tarfile.open(archive_path, "w:gz") as tar:
        for p in candidates:
            tar.add(p, arcname=p.name)

    for p in candidates:
        p.unlink()

    print(f"Archived {len(candidates)} snapshot(s) → {archive_path}")
    return 0
