"""Tests for drift_watch.snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from drift_watch.snapshot import SnapshotError, load_snapshot, save_snapshot


SAMPLE_CONFIG = {
    "api": {"replicas": 3, "image": "api:1.2"},
    "worker": {"replicas": 1, "image": "worker:0.9"},
}


# ---------------------------------------------------------------------------
# save_snapshot
# ---------------------------------------------------------------------------

def test_save_creates_file(tmp_path):
    dest = tmp_path / "snap.json"
    save_snapshot(SAMPLE_CONFIG, dest)
    assert dest.exists()


def test_save_content_is_valid_json(tmp_path):
    dest = tmp_path / "snap.json"
    save_snapshot(SAMPLE_CONFIG, dest)
    payload = json.loads(dest.read_text())
    assert payload["version"] == 1
    assert "captured_at" in payload
    assert payload["services"] == SAMPLE_CONFIG


def test_save_creates_parent_directories(tmp_path):
    dest = tmp_path / "nested" / "dir" / "snap.json"
    save_snapshot(SAMPLE_CONFIG, dest)
    assert dest.exists()


def test_save_raises_snapshot_error_on_bad_path():
    with pytest.raises(SnapshotError, match="Could not write"):
        # A directory cannot be opened as a file for writing.
        save_snapshot(SAMPLE_CONFIG, "/dev/null/cannot_write_here/snap.json")


# ---------------------------------------------------------------------------
# load_snapshot
# ---------------------------------------------------------------------------

def test_load_returns_services(tmp_path):
    dest = tmp_path / "snap.json"
    save_snapshot(SAMPLE_CONFIG, dest)
    services = load_snapshot(dest)
    assert services == SAMPLE_CONFIG


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot(tmp_path / "nonexistent.json")


def test_load_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json!!")
    with pytest.raises(SnapshotError, match="not valid JSON"):
        load_snapshot(bad)


def test_load_missing_services_key_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"version": 1}))
    with pytest.raises(SnapshotError, match="missing required 'services'"):
        load_snapshot(bad)


def test_load_non_mapping_services_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"version": 1, "services": ["a", "b"]}))
    with pytest.raises(SnapshotError, match="must be a mapping"):
        load_snapshot(bad)


# ---------------------------------------------------------------------------
# round-trip
# ---------------------------------------------------------------------------

def test_roundtrip(tmp_path):
    dest = tmp_path / "rt.json"
    save_snapshot(SAMPLE_CONFIG, dest)
    assert load_snapshot(dest) == SAMPLE_CONFIG
