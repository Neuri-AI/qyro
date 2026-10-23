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
