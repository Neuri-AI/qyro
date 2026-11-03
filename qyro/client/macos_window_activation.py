"""Activate a source-mode macOS desktop application at first presentation.

This module does not load AppKit on non-macOS platforms and does not depend on
PyObjC. Activation is restricted to initial window presentation; PSX updates
must not steal focus from other applications.
"""
from __future__ import annotations

import ctypes
import sys
import warnings


def activate_macos_application() -> bool:
    if sys.platform != "darwin":
        return False
    try:
        ctypes.CDLL("/System/Library/Frameworks/AppKit.framework/AppKit")
        objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib")

        cls = objc.objc_getClass
        cls.argtypes = [ctypes.c_char_p]
        cls.restype = ctypes.c_void_p
        sel = objc.sel_registerName
        sel.argtypes = [ctypes.c_char_p]
        sel.restype = ctypes.c_void_p
        application_type = cls(b"NSApplication")
        if not application_type:
            raise RuntimeError("NSApplication unavailable")

        # Avoid reassigning objc_msgSend.argtypes on a shared ctypes symbol:
        # declare independent typed call sites for each message signature.
        send_object = ctypes.CFUNCTYPE(
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        )(("objc_msgSend", objc))
        send_boolean = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool
        )(("objc_msgSend", objc))
        application = send_object(
            application_type, sel(b"sharedApplication")
        )
        if not application:
            raise RuntimeError("NSApplication.sharedApplication unavailable")
        # This is a one-time request to bring the just-launched application
        # forward, not a permanent topmost window flag.
        send_boolean(application, sel(b"activateIgnoringOtherApps:"), True)
        return True
    except (OSError, AttributeError, RuntimeError, ValueError, TypeError) as exc:
        warnings.warn(
            f"Could not activate macOS application window: {exc}",
            RuntimeWarning, stacklevel=2,
        )
        return False
