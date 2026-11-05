"""Android p4a root lookup must find extracted Velto settings and assets."""
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

from qyro.adapters.environment.system_environment import SystemEnvironmentAdapter
from qyro.domain.entities import PlatformType


def test_android_uses_extracted_cwd_even_if_marked_frozen(tmp_path, monkeypatch):
    app = tmp_path / "files" / "app"
    (app / "settings").mkdir(parents=True)
    (app / "settings" / "base.json").write_text('{"framework":"PySide6"}')
    monkeypatch.chdir(app)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python" / "binary"))
    monkeypatch.setattr(
        SystemEnvironmentAdapter, "get_platform",
        lambda self: PlatformType.ANDROID,
    )
    env = SystemEnvironmentAdapter()
    assert env.get_root_dir() == app
    assert env.get_bundle_dir() == app


def test_android_prefers_main_module_directory(tmp_path, monkeypatch):
    app = tmp_path / "app"
    (app / "settings").mkdir(parents=True)
    (app / "settings" / "base.json").write_text('{"framework":"PySide6"}')
    wrong_cwd = tmp_path / "elsewhere"
    wrong_cwd.mkdir()
    monkeypatch.chdir(wrong_cwd)
    monkeypatch.setattr(
        SystemEnvironmentAdapter, "get_platform",
        lambda self: PlatformType.ANDROID,
    )
    monkeypatch.setitem(
        sys.modules, "__main__", SimpleNamespace(__file__=str(app / "main.py"))
    )
    assert SystemEnvironmentAdapter().get_root_dir() == app


def test_android_respects_explicit_custom_root(tmp_path, monkeypatch):
    monkeypatch.setattr(
        SystemEnvironmentAdapter, "get_platform",
        lambda self: PlatformType.ANDROID,
    )
    assert SystemEnvironmentAdapter(custom_root=tmp_path).get_root_dir() == tmp_path


def test_desktop_root_resolution_unchanged(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n")
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.chdir(child)
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.setattr(
        SystemEnvironmentAdapter, "get_platform",
        lambda self: PlatformType.LINUX,
    )
    assert SystemEnvironmentAdapter().get_root_dir() == tmp_path
