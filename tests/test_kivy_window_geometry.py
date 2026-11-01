"""Kivy startup must stay reachable on macOS Retina even for giant base.json sizes."""

from __future__ import annotations

import ctypes
import sys
import types

import pytest

from qyro.client import kivy_window_geometry as geometry


@pytest.mark.parametrize(
    ("requested", "available", "expected"),
    [
        ((800, 600), (1600, 900), (800, 600)),
        ((1600, 1200), (1600, 900), (1600, 900)),
        ((2560, 1600), (1648, 929), (1648, 929)),
        ((800, 600), (320, 240), (320, 240)),
    ],
)
def test_oversized_window_clamped_to_visible_screen_points(
    requested, available, expected, caplog,
):
    assert geometry.visible_kivy_window_size(requested, available=available) == expected
    if expected != requested:
        assert "exceeds usable display" in caplog.text


def test_unavailable_macos_monitor_defaults_to_known_safe_window(monkeypatch):
    monkeypatch.setattr(geometry.sys, "platform", "darwin")
    monkeypatch.setattr(geometry, "macos_usable_display_size", lambda: None)
    assert geometry.visible_kivy_window_size((2560, 1600)) == (800, 600)


def test_unavailable_non_macos_monitor_preserves_requested_size(monkeypatch):
    monkeypatch.setattr(geometry.sys, "platform", "linux")
    monkeypatch.setattr(geometry, "macos_usable_display_size", lambda: None)
    assert geometry.visible_kivy_window_size((2560, 1600)) == (2560, 1600)


def test_non_mac_does_not_query_cocoa(monkeypatch):
    monkeypatch.setattr(geometry.sys, "platform", "linux")
    assert geometry.macos_usable_display_size() is None


def test_appkit_visible_frame_uses_actual_safe_area(monkeypatch):
    monkeypatch.setattr(geometry.sys, "platform", "darwin")
    frame = types.SimpleNamespace(
        size=types.SimpleNamespace(width=1512.0, height=875.0)
    )
    screen = types.SimpleNamespace(visibleFrame=lambda: frame)
    ns_screen = types.SimpleNamespace(mainScreen=lambda: screen)
    monkeypatch.setitem(sys.modules, "AppKit", types.SimpleNamespace(NSScreen=ns_screen))
    assert geometry.macos_usable_display_size() == (1512, 875)


def test_coregraphics_fallback_reads_logical_points_without_retina_multiplier(
    monkeypatch,
):
    monkeypatch.setattr(geometry.sys, "platform", "darwin")
    monkeypatch.setitem(sys.modules, "AppKit", None)

    class Function:
        def __init__(self, fn):
            self.fn = fn

        def __call__(self, *args):
            return self.fn(*args)

    class FakeCore:
        CGMainDisplayID = Function(lambda: 1)

        @staticmethod
        def bounds(_display):
            result = FakeCore.CGDisplayBounds.restype()
            result.size.width = 1680
            result.size.height = 1029
            return result

        CGDisplayBounds = Function(bounds)

    monkeypatch.setattr(ctypes, "CDLL", lambda path: FakeCore())
    assert geometry.macos_usable_display_size() == (1648, 929)
    assert geometry.visible_kivy_window_size((2560, 1600)) == (1648, 929)


@pytest.mark.skipif(sys.platform != "darwin", reason="Requires macOS")
def test_native_macos_monitor_geometry_uses_screen_points():
    actual = geometry.macos_usable_display_size()
    if actual is None:
        pytest.skip("macOS CI host has no CoreGraphics display")
    assert 100 <= actual[0] <= 10000
    assert 100 <= actual[1] <= 10000
