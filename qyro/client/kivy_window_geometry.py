"""Safe Kivy desktop startup geometry (window points, never GL pixels).

The user's requested size is a preference, not permission to position an
unreachable native window outside the physical desktop. On macOS, retrieve the
usable display size *before* importing Kivy's Window provider. This module
must not import Kivy or modify its global DPI/density configuration.
"""

from __future__ import annotations

import ctypes
import logging
import math
import sys

_LOG = logging.getLogger(__name__)


def macos_usable_display_size() -> tuple[int, int] | None:
    """Return main screen work area in Cocoa points, if available.

    Prefer AppKit's visibleFrame when PyObjC is installed. Otherwise use
    CoreGraphics display bounds with a conservative titlebar/menu/Dock budget.
    CGDisplayBounds is in logical screen coordinates even on Retina screens.
    """
    if sys.platform != "darwin":
        return None

    try:
        from AppKit import NSScreen  # optional dependency

        screen = NSScreen.mainScreen()
        if screen is not None:
            frame = screen.visibleFrame()
            width, height = float(frame.size.width), float(frame.size.height)
            if math.isfinite(width) and math.isfinite(height) and width > 0 and height > 0:
                return int(width), int(height)
    except (ImportError, AttributeError, ValueError, TypeError):
        pass
    except Exception:
        _LOG.debug("Could not read macOS AppKit visibleFrame", exc_info=True)

    # No optional Objective-C bridge is required by Velto. Query the native C
    # CoreGraphics API instead, retaining logical Cocoa points, not pixels.
    class _Point(ctypes.Structure):
        _fields_ = (("x", ctypes.c_double), ("y", ctypes.c_double))

    class _Size(ctypes.Structure):
        _fields_ = (("width", ctypes.c_double), ("height", ctypes.c_double))

    class _Rect(ctypes.Structure):
        _fields_ = (("origin", _Point), ("size", _Size))

    try:
        core = ctypes.CDLL(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        core.CGMainDisplayID.argtypes = ()
        core.CGMainDisplayID.restype = ctypes.c_uint32
        core.CGDisplayBounds.argtypes = (ctypes.c_uint32,)
        core.CGDisplayBounds.restype = _Rect
        rect = core.CGDisplayBounds(core.CGMainDisplayID())
        width, height = float(rect.size.width), float(rect.size.height)
        if math.isfinite(width) and math.isfinite(height) and width > 0 and height > 0:
            # CGDisplayBounds includes the menu bar and Dock. Reserve space
            # for both plus the SDL title bar when AppKit is unavailable.
            return max(1, int(width) - 32), max(1, int(height) - 100)
    except (OSError, AttributeError, TypeError, ValueError):
        _LOG.warning("Could not read macOS display bounds; window size is unbounded")
    return None


def visible_kivy_window_size(
    requested: tuple[int, int], *, available: tuple[int, int] | None = None,
) -> tuple[int, int]:
    """Fit requested *window-point* dimensions on the visible display.

    If no screen bounds can be determined, preserve the preference rather
    than silently guessing at an arbitrary Retina scale factor.
    """
    if available is None:
        available = macos_usable_display_size()
    if available is None:
        return requested
    width, height = requested
    usable_width, usable_height = available
    if usable_width <= 0 or usable_height <= 0:
        return requested
    actual = min(width, usable_width), min(height, usable_height)
    if actual != requested:
        _LOG.warning(
            "Kivy window %sx%s exceeds usable display %sx%s points; "
            "starting at %sx%s to keep the window visible and interactive",
            width, height, usable_width, usable_height, *actual,
        )
    return actual
