"""Development notifications never mutate UI from the receiver thread."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from qyro.client.velto_context import VeltoContext


def test_receiver_schedules_refresh_on_renderer_owner_thread(monkeypatch):
    scheduled = []
    renderer = SimpleNamespace(schedule_ui=scheduled.append)
    context = object.__new__(VeltoContext)
    context._mounted = True
    context._renderer = renderer
    context._app = object()
    dispatched = []
    monkeypatch.setattr(context, "_apply_development_change", dispatched.append)
    context._on_development_change(("views/main.py",))
    assert dispatched == []
    assert len(scheduled) == 1
    scheduled[0]()
    assert dispatched == [("views/main.py",)]


def test_unmounted_context_drops_changes_without_scheduling():
    scheduled = []
    context = object.__new__(VeltoContext)
    context._mounted = False
    context._renderer = SimpleNamespace(schedule_ui=scheduled.append)
    context._on_development_change(("views/main.py",))
    assert not scheduled


def test_source_refresh_invokes_psx_once_on_ui_thread(monkeypatch, tmp_path):
    import os
    import sys
    import types

    entry = tmp_path / "main.py"
    entry.write_text("class Demo: pass", encoding="utf-8")
    monkeypatch.setenv("PSX_SOURCE_ENTRY", str(entry))
    calls = []
    fake_devtools = types.ModuleType("psx.devtools")
    fake_refresh = types.ModuleType("psx.devtools.coordinated_refresh")
    fake_refresh.refresh_context_source = lambda *args: calls.append(args)
    fake_psx = types.ModuleType("psx")
    fake_psx.__path__ = []
    fake_devtools.__path__ = []
    monkeypatch.setitem(sys.modules, "psx", fake_psx)
    monkeypatch.setitem(sys.modules, "psx.devtools", fake_devtools)
    monkeypatch.setitem(sys.modules, "psx.devtools.coordinated_refresh", fake_refresh)
    context = object.__new__(VeltoContext)
    context._mounted = True
    context._app = object()
    context._apply_development_change(("main.py",))
    assert len(calls) == 1
    assert calls[0][0] is context
    assert calls[0][1] == entry
    assert calls[0][2] == ("main.py",)
