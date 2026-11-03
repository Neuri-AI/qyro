"""macOS Dock icon support for source and frozen Velto applications.

Kivy's SDL2 Window.icon changes the window-provider icon, which does not
necessarily update the macOS Dock tile. AppKit owns the process-level icon.
Avoid introducing a PyObjC dependency into the otherwise portable runtime.
"""
from __future__ import annotations

import ctypes
import sys
import warnings
from pathlib import Path


def set_macos_dock_icon(path: str) -> bool:
    """Set NSApplication's icon from a PNG/ICNS on the macOS UI thread.

    Returns False (and warns) if the image cannot be loaded or AppKit is
    unavailable. Non-macOS systems never load the Objective-C runtime.
    """
    if sys.platform != "darwin":
        return False
    icon = Path(path)
    if not icon.is_file():
        warnings.warn(f"macOS Dock icon does not exist: {icon}", RuntimeWarning, stacklevel=2)
        return False

    # objc_msgSend's signature is selector-specific. All sends here return
    # object pointers except isValid (BOOL). Keep the signatures explicit.
    try:
        objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib")
        get_class = objc.objc_getClass
        get_class.argtypes = [ctypes.c_char_p]
        get_class.restype = ctypes.c_void_p
        register_selector = objc.sel_registerName
        register_selector.argtypes = [ctypes.c_char_p]
        register_selector.restype = ctypes.c_void_p

        def send(receiver: int, selector: str, arg: int | bytes | None = None) -> int:
            method = objc.objc_msgSend
            method.restype = ctypes.c_void_p
            if isinstance(arg, bytes):
                method.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p]
                return int(method(receiver, register_selector(selector.encode()), arg) or 0)
            if arg is not None:
                method.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
                return int(method(receiver, register_selector(selector.encode()), arg) or 0)
            method.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            return int(method(receiver, register_selector(selector.encode())) or 0)

        ns_string = get_class(b"NSString")
        ns_image = get_class(b"NSImage")
        ns_app = get_class(b"NSApplication")
        if not (ns_string and ns_image and ns_app):
            raise RuntimeError("NSString, NSImage or NSApplication unavailable")

        name = send(ns_string, "stringWithUTF8String:", str(icon).encode("utf-8"))
        if not name:
            raise RuntimeError("Could not convert icon path to NSString")
        image = send(send(ns_image, "alloc"), "initWithContentsOfFile:", name)
        if not image:
            raise RuntimeError("NSImage could not load the icon")
        try:
            application = send(ns_app, "sharedApplication")
            if not application:
                raise RuntimeError("NSApplication.sharedApplication unavailable")
            send(application, "setApplicationIconImage:", image)
        finally:
            send(image, "release")
        return True
    except (OSError, AttributeError, RuntimeError, ValueError, TypeError) as exc:
        warnings.warn(
            f"Could not set macOS Dock icon {str(icon)!r}: {exc}",
            RuntimeWarning, stacklevel=2,
        )
        return False
