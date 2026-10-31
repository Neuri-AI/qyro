"""Development-only settings merge and frozen runtime exclusion."""
import json
from pathlib import Path

import pytest

from qyro.adapters.settings.json_settings import JsonSettingsAdapter
from qyro.domain.entities import PlatformType


class Environment:
    def __init__(self, root: Path, frozen=False):
        self.root, self.frozen = root, frozen

    def is_frozen(self):
        return self.frozen

    def get_root_dir(self):
        return self.root

    def get_bundle_dir(self):
        return self.root

    def get_platform(self):
        return PlatformType.LINUX


def write_settings(root: Path):
    settings = root / "settings"
    settings.mkdir()
    for name, value in {
        "base": {"app_name": "Example", "hot_reload": {"enabled": False,
                 "module_reload": {"third_party": "restart"}, "debounce_ms": 300}},
        "linux": {"hot_reload": {"debounce_ms": 250}},
        "development": {"hot_reload": {"enabled": True, "debounce_ms": 150}},
    }.items():
        (settings / (name + ".json")).write_text(json.dumps(value), encoding="utf-8")
    return settings


def test_source_development_profile_preserves_base_and_platform_siblings(tmp_path, monkeypatch):
    write_settings(tmp_path)
    monkeypatch.setenv("VELTO_DEVELOPMENT", "1")
    config = JsonSettingsAdapter(Environment(tmp_path)).get_raw_settings()
    assert config["hot_reload"] == {
        "enabled": True, "debounce_ms": 150,
        "module_reload": {"third_party": "restart"},
    }


def test_regular_source_launch_ignores_development_overrides(tmp_path, monkeypatch):
    write_settings(tmp_path)
    monkeypatch.delenv("VELTO_DEVELOPMENT", raising=False)
    config = JsonSettingsAdapter(Environment(tmp_path)).get_raw_settings()
    assert config["hot_reload"]["enabled"] is False
    assert config["hot_reload"]["debounce_ms"] == 250


def test_frozen_launch_does_not_read_development_profile(tmp_path, monkeypatch):
    write_settings(tmp_path)
    monkeypatch.setenv("VELTO_DEVELOPMENT", "1")
    config = JsonSettingsAdapter(Environment(tmp_path, frozen=True)).get_raw_settings()
    assert config["hot_reload"]["enabled"] is False


def test_malformed_explicit_development_configuration_is_rejected(tmp_path, monkeypatch):
    settings = write_settings(tmp_path)
    (settings / "development.json").write_text('["invalid"]', encoding="utf-8")
    monkeypatch.setenv("VELTO_DEVELOPMENT", "1")
    with pytest.raises(ValueError, match="development.json"):
        JsonSettingsAdapter(Environment(tmp_path)).get_raw_settings()
