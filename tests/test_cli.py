"""Tests for the drift_watch.cli module."""

import json
from pathlib import Path

import pytest

from drift_watch.cli import run


@pytest.fixture()
def declared_file(tmp_path: Path) -> Path:
    config = tmp_path / "declared.yaml"
    config.write_text(
        "web:\n  replicas: 3\n  image: nginx:1.25\nworker:\n  replicas: 2\n  image: myapp:latest\n"
    )
    return config


@pytest.fixture()
def live_matching_file(tmp_path: Path) -> Path:
    config = tmp_path / "live_ok.yaml"
    config.write_text(
        "web:\n  replicas: 3\n  image: nginx:1.25\nworker:\n  replicas: 2\n  image: myapp:latest\n"
    )
    return config


@pytest.fixture()
def live_drifted_file(tmp_path: Path) -> Path:
    config = tmp_path / "live_drifted.yaml"
    config.write_text(
        "web:\n  replicas: 5\n  image: nginx:1.25\nworker:\n  replicas: 2\n  image: myapp:latest\n"
    )
    return config


def test_no_drift_exits_zero(declared_file, live_matching_file):
    code = run([str(declared_file), str(live_matching_file), "--exit-code"])
    assert code == 0


def test_drift_exits_one_with_flag(declared_file, live_drifted_file):
    code = run([str(declared_file), str(live_drifted_file), "--exit-code"])
    assert code == 1


def test_drift_exits_zero_without_flag(declared_file, live_drifted_file):
    code = run([str(declared_file), str(live_drifted_file)])
    assert code == 0


def test_missing_declared_file_exits_two(tmp_path, live_matching_file):
    code = run([str(tmp_path / "nope.yaml"), str(live_matching_file)])
    assert code == 2


def test_missing_live_file_exits_two(tmp_path, declared_file):
    code = run([str(declared_file), str(tmp_path / "nope.yaml")])
    assert code == 2


def test_json_output_is_valid(declared_file, live_drifted_file, capsys):
    run([str(declared_file), str(live_drifted_file), "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert any(r["service"] == "web" for r in data)


def test_text_output_contains_service_name(declared_file, live_drifted_file, capsys):
    run([str(declared_file), str(live_drifted_file), "--format", "text"])
    captured = capsys.readouterr()
    assert "web" in captured.out
