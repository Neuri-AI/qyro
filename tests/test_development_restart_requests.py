"""Unsafe native changes request supervisor restart; first imports do not."""
from types import SimpleNamespace
import sys

import pytest

from qyro.client.development_changes import DevelopmentChangeReceiver
from qyro.client.velto_context import VeltoContext


def test_restart_request_rejects_unrecognized_reason():
    receiver = DevelopmentChangeReceiver(lambda _: None)
    with pytest.raises(ValueError):
        receiver.request_restart("any_change")


def test_native_extension_replacement_requests_restart(tmp_path, monkeypatch):
    import importlib.machinery
    from unittest.mock import Mock
    suffix = importlib.machinery.EXTENSION_SUFFIXES[-1]
    binary = tmp_path / ("extension" + suffix)
    source = tmp_path / "main.py"
    source.write_text("class Demo: pass", encoding="utf-8")
    monkeypatch.setenv("PSX_SOURCE_ENTRY", str(source))
    monkeypatch.setenv("VELTO_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setitem(sys.modules, "dev_native_mock", SimpleNamespace(__file__=str(binary)))
    ctx = object.__new__(VeltoContext)
    ctx._mounted = True
    ctx._app = object()
    ctx._development_receiver = SimpleNamespace(request_restart=Mock(return_value=True))
    ctx._apply_development_change((binary.name,))
    ctx._development_receiver.request_restart.assert_called_once_with(
        "loaded_native_extension_changed"
    )


def test_unloaded_binary_does_not_request_restart(tmp_path, monkeypatch):
    import importlib.machinery
    from unittest.mock import Mock
    suffix = importlib.machinery.EXTENSION_SUFFIXES[-1]
    binary = tmp_path / ("new_native" + suffix)
    source = tmp_path / "main.py"
    source.write_text("class Demo: pass", encoding="utf-8")
    monkeypatch.setenv("PSX_SOURCE_ENTRY", str(source))
    monkeypatch.setenv("VELTO_PROJECT_ROOT", str(tmp_path))
    ctx = object.__new__(VeltoContext)
    ctx._mounted = True
    ctx._app = object()
    ctx._development_receiver = SimpleNamespace(request_restart=Mock(return_value=True))
    # The existing PSX updater rejects unrelated binaries without side effects.
    ctx._apply_development_change((binary.name,))
    ctx._development_receiver.request_restart.assert_not_called()


def test_supported_unsafe_restart_reasons_require_connected_supervisor():
    receiver = DevelopmentChangeReceiver(lambda _: None)
    for reason in ("interpreter_changed", "unsafe_global_initialization",
                   "external_resource_incompatible"):
        assert receiver.request_restart(reason) is False


def test_development_backend_rollback_is_source_only(monkeypatch):
    from qyro.domain.entities import AppMetadata
    context = object.__new__(VeltoContext)
    boot = VeltoContext._global_boot_info
    try:
        VeltoContext._global_boot_info = {
            "is_frozen": False,
            "metadata": AppMetadata(app_name="Restart recovery", raw_settings={"framework": "kivy"}),
        }
        monkeypatch.setenv("VELTO_DEVELOPMENT", "1")
        monkeypatch.setenv("VELTO_RECOVERY_FRAMEWORK", "tkinter")
        assert context.app_settings["framework"] == "tkinter"
        assert context.metadata.raw_settings["framework"] == "kivy"
        VeltoContext._global_boot_info["is_frozen"] = True
        assert context.app_settings["framework"] == "kivy"
    finally:
        VeltoContext._global_boot_info = boot


def test_root_host_change_requests_restart_without_discarding_live_app(tmp_path, monkeypatch):
    import types
    from unittest.mock import Mock
    import qyro.client.development_state as development_state

    source = tmp_path / "main.py"
    source.write_text("class Demo: pass", encoding="utf-8")
    monkeypatch.setenv("PSX_SOURCE_ENTRY", str(source))
    monkeypatch.setenv("VELTO_PROJECT_ROOT", str(tmp_path))

    class RootHostTransitionRequiresRestart(Exception):
        pass

    psx = types.ModuleType("psx")
    psx.__path__ = []
    core = types.ModuleType("psx.core")
    core.__path__ = []
    errors = types.ModuleType("psx.core.errors")
    errors.RootHostTransitionRequiresRestart = RootHostTransitionRequiresRestart
    devtools = types.ModuleType("psx.devtools")
    devtools.__path__ = []
    refresh = types.ModuleType("psx.devtools.coordinated_refresh")
    def reject_root_change(*_args):
        raise RootHostTransitionRequiresRestart("root type changed")
    refresh.refresh_context_source = reject_root_change
    for name, module in (
        ("psx", psx), ("psx.core", core), ("psx.core.errors", errors),
        ("psx.devtools", devtools), ("psx.devtools.coordinated_refresh", refresh),
    ):
        monkeypatch.setitem(sys.modules, name, module)

    saved = Mock(return_value=True)
    monkeypatch.setattr(development_state, "capture_restart_state", saved)
    monkeypatch.setattr(VeltoContext, "app_settings", property(
        lambda _self: {"hot_reload": {"preserve_state": False}}))
    context = object.__new__(VeltoContext)
    context._mounted = True
    context._app = object()
    context._development_receiver = SimpleNamespace(
        request_restart=Mock(return_value=True))
    context._apply_development_change(("main.py",))
    saved.assert_called_once_with(context)
    context._development_receiver.request_restart.assert_called_once_with(
        "root_host_changed")


def test_root_host_restart_reason_requires_connected_supervisor():
    assert DevelopmentChangeReceiver(lambda _: None).request_restart(
        "root_host_changed") is False
