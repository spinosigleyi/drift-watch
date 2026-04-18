"""Tests for drift_watch.loader."""

from __future__ import annotations

import json
import textwrap

import pytest

from drift_watch.loader import ConfigLoadError, load_declared_config, load_live_config


# ---------------------------------------------------------------------------
# load_declared_config
# ---------------------------------------------------------------------------

def test_load_yaml_file(tmp_path):
    config_file = tmp_path / "services.yaml"
    config_file.write_text(
        textwrap.dedent("""\
        api:
          replicas: 2
          image: api:1.0.0
        worker:
          replicas: 5
          image: worker:2.3.1
        """)
    )
    result = load_declared_config(str(config_file))
    assert result == {
        "api": {"replicas": 2, "image": "api:1.0.0"},
        "worker": {"replicas": 5, "image": "worker:2.3.1"},
    }


def test_load_json_file(tmp_path):
    config_file = tmp_path / "services.json"
    payload = {"svc": {"port": 8080, "env": "staging"}}
    config_file.write_text(json.dumps(payload))
    result = load_declared_config(str(config_file))
    assert result == payload


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigLoadError, match="not found"):
        load_declared_config(str(tmp_path / "nonexistent.yaml"))


def test_malformed_yaml_raises(tmp_path):
    config_file = tmp_path / "bad.yaml"
    config_file.write_text(": : : invalid yaml :::")
    with pytest.raises(ConfigLoadError, match="Failed to parse"):
        load_declared_config(str(config_file))


def test_non_mapping_yaml_raises(tmp_path):
    config_file = tmp_path / "list.yaml"
    config_file.write_text("- item1\n- item2\n")
    with pytest.raises(ConfigLoadError, match="Expected a mapping"):
        load_declared_config(str(config_file))


def test_malformed_json_raises(tmp_path):
    """A JSON file with invalid syntax should raise ConfigLoadError."""
    config_file = tmp_path / "bad.json"
    config_file.write_text("{not: valid json}")
    with pytest.raises(ConfigLoadError, match="Failed to parse"):
        load_declared_config(str(config_file))


def test_unsupported_extension_raises(tmp_path):
    """A file with an unrecognised extension should raise ConfigLoadError."""
    config_file = tmp_path / "services.toml"
    config_file.write_text("[api]\nreplicas = 2\n(ConfigLoadError, match="Unsupported file format"):
        load_declared_config(str(config_file))


# ---------------------------------------------------------------------------
# load_live_config
# ---------------------------------------------------------------------------

def test_live():
    source = {"api": {"replicas": 3, "image": "api:1.1.0"}}
    result = load_live_config("api", source)
    assert result == {"replicas": 3, "image": "api:1.1.0"}


def test_live_config_missing_service_returns_empty():
    result = load_live_config("ghost-service", {})
    assert result == {}


def test_live_config_returns_copy():
    """Mutating the returned dict must not affect the source."""
    source = {"svc": {"port": 80}}
    result = load_live_config("svc", source)
    result["port"] = 9999
    assert source["svc"]["port"] == 80
