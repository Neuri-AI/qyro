"""Tk windows are raised once at startup without permanent topmost flags."""
from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from qyro.client.velto_context import VeltoContext


class TkWindowProbe:
    def __init__(self):
        self.calls = []
        self.idle_callback = None
        self.exists = True

    def winfo_exists(self):
        return self.exists

    def deiconify(self):
        self.calls.append("deiconify")

    def lift(self):
        self.calls.append("lift")

    def focus_force(self):
        self.calls.append("focus_force")

    def after_idle(self, callback):
        assert self.idle_callback is None
        self.idle_callback = callback


def test_tk_activation_is_scheduled_after_window_setup(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    window = TkWindowProbe()
    VeltoContext._activate_tk_window(window)
    assert window.calls == []
    assert callable(window.idle_callback)
    window.idle_callback()
    assert window.calls == ["deiconify", "lift", "focus_force"]


def test_tk_activation_does_not_raise_destroyed_window(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    window = TkWindowProbe()
    VeltoContext._activate_tk_window(window)
    window.exists = False
    window.idle_callback()
    assert window.calls == []


def test_macos_activates_application_before_tk_focus(monkeypatch):
    from qyro.client import macos_window_activation

    monkeypatch.setattr(sys, "platform", "darwin")
    window = TkWindowProbe()
    monkeypatch.setattr(
        macos_window_activation, "activate_macos_application",
        lambda: window.calls.append("app_activate") or True
    )
    VeltoContext._activate_tk_window(window)
    window.idle_callback()
    assert window.calls == [
        "deiconify", "lift", "app_activate", "focus_force",
    ]


def test_non_macos_never_loads_appkit(monkeypatch):
    from qyro.client.macos_window_activation import activate_macos_application
    monkeypatch.setattr(sys, "platform", "linux")
    assert activate_macos_application() is False
