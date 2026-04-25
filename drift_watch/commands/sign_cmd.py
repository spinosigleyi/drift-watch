"""sign_cmd — sign a snapshot file with an HMAC-SHA256 digest and verify signatures."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from argparse import ArgumentParser, _SubParsersAction
from pathlib import Path
from typing import Optional

_SIG_KEY = "_signature"


def add_parser(subparsers: _SubParsersAction) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser(
        "sign",
        help="Sign or verify a snapshot file using HMAC-SHA256.",
    )
    p.add_argument("snapshot", help="Path to the snapshot JSON file.")
    p.add_argument(
        "--verify",
        action="store_true",
        default=False,
        help="Verify an existing signature instead of creating one.",
    )
    p.add_argument(
        "--key-env",
        default="DRIFT_WATCH_SIGN_KEY",
        metavar="ENV_VAR",
        help="Environment variable that holds the signing secret (default: DRIFT_WATCH_SIGN_KEY).",
    )
    p.set_defaults(func=run_sign)


def _load_raw(path: Path) -> dict:  # type: ignore[type-arg]
    with path.open() as fh:
        return json.load(fh)


def _canonical_bytes(data: dict) -> bytes:  # type: ignore[type-arg]
    """Serialise *data* (without any existing signature) deterministically."""
    clean = {k: v for k, v in data.items() if k != _SIG_KEY}
    return json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()


def _compute_sig(data: dict, secret: str) -> str:  # type: ignore[type-arg]
    return hmac.new(
        secret.encode(),
        _canonical_bytes(data),
        hashlib.sha256,
    ).hexdigest()


def run_sign(args) -> int:  # type: ignore[no-untyped-def]
    path = Path(args.snapshot)
    if not path.exists():
        print(f"[sign] error: file not found: {path}")
        return 1

    secret: Optional[str] = os.environ.get(args.key_env)
    if not secret:
        print(f"[sign] error: environment variable '{args.key_env}' is not set.")
        return 1

    try:
        data = _load_raw(path)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[sign] error loading snapshot: {exc}")
        return 1

    sig = _compute_sig(data, secret)

    if args.verify:
        existing = data.get(_SIG_KEY, "")
        if hmac.compare_digest(existing, sig):
            print(f"[sign] ✓ signature valid: {path}")
            return 0
        print(f"[sign] ✗ signature mismatch: {path}")
        return 1

    data[_SIG_KEY] = sig
    with path.open("w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"[sign] signed: {path}  ({sig[:16]}…)")
    return 0
