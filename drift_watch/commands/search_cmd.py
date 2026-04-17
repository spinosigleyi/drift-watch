"""search_cmd – search snapshots for services matching a pattern."""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import List, Tuple


def add_parser(subparsers):
    p = subparsers.add_parser("search", help="Search snapshots for matching services")
    p.add_argument("pattern", help="Glob pattern to match service names")
    p.add_argument(
        "--snapshot-dir",
        default=".drift_watch/snapshots",
        help="Directory containing snapshot files",
    )
    p.add_argument(
        "--drifted-only",
        action="store_true",
        help="Only return services with drift",
    )
    p.set_defaults(func=run_search)


def _collect_matches(
    snapshot_dir: str, pattern: str, drifted_only: bool
) -> List[Tuple[str, str, str]]:
    """Return list of (snapshot_file, service_name, status) tuples."""
 = []
    base = Path(snapshot_dir)
    if not base.exists():
        return results
    for snap_file in sorted(base.glob(":
            data = json.loads(snap_file.read_text())
            services = data.get("services", {})
        except (json.JSONDecodeError, OSError):
            continue
        for svc_name, svc_data in services.items():
            if not fnmatch.fnmatch(svc_name, pattern):
                continue
            status = svc_data.get("status", "unknown")
            if drifted_only and status not in ("drifted", "missing"):
                continue
            results.append((snap_file.name, svc_name, status))
    return results


def run_search(args) -> int:
    matches = _collect_matches(args.snapshot_dir, args.pattern, args.drifted_only)
    if not matches:
        print("No matching services found.")
        return 0
    printSnapshot':<40} {'Service':<30} {'Status'}")
    print("-" * 80)
    for snap, svc, status in matches:
        print(f"{snap: {status}")
    print(f"\n{len(matches)} result(s) found.")
    return 0
