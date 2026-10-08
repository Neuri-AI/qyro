"""
Framework Factory.
Detects available UI toolkits or instantiates the user's requested engine backend.
"""

from importlib import import_module
from typing import Optional, Type
from qyro.application.ports.ui_framework import IUIFrameworkPort
from qyro.domain.errors import FrameworkNotAvailableError


class FrameworkFactory:
    """Instantiates framework adapters based on preference or automatic detection."""

    # Importing Qt and Tk in the same macOS process can make Tk fail during
    # startup.  Keep the adapters as import specifications instead of eagerly
    # importing every optional UI backend when Qyro itself is imported.
    _FRAMEWORK_REGISTRY = {
        "pyside6": (".pyside6_adapter", "PySide6Adapter"),
        "pyqt6": (".pyqt6_adapter", "PyQt6Adapter"),
        "pyside2": (".pyside2_adapter", "PySide2Adapter"),
        "pyqt5": (".pyqt5_adapter", "PyQt5Adapter"),
        "kivy": (".kivy_adapter", "KivyAdapter"),
        "tkinter": (".tkinter_adapter", "TkinterAdapter"),
        "headless": (".headless_adapter", "HeadlessAdapter"),
    }

    @classmethod
    def _adapter_class(cls, name: str) -> Type[IUIFrameworkPort]:
        module_name, class_name = cls._FRAMEWORK_REGISTRY[name]
        module = import_module(module_name, package=__package__)
        return getattr(module, class_name)

    @classmethod
    def create(cls, name: Optional[str] = None) -> IUIFrameworkPort:
        if name:
            normalized = name.strip().lower()
            if normalized not in cls._FRAMEWORK_REGISTRY:
                raise FrameworkNotAvailableError(
                    name,
                    f"Supported frameworks: {', '.join(cls._FRAMEWORK_REGISTRY.keys())}"
                )
            adapter_cls = cls._adapter_class(normalized)
            adapter = adapter_cls()
            if not adapter.is_available():
                raise FrameworkNotAvailableError(adapter.framework_name)
            return adapter

        # Auto-detect in order of preference
        preference = list(cls._FRAMEWORK_REGISTRY)
        for name in preference:
            candidate_cls = cls._adapter_class(name)
            candidate = candidate_cls()
            if candidate.is_available():
                return candidate

        return cls._adapter_class("headless")()
