"""
Framework Factory.
Detects available UI toolkits or instantiates the user's requested engine backend.
"""

from typing import Optional
from qyro.application.ports.ui_framework import IUIFrameworkPort
from qyro.domain.errors import FrameworkNotAvailableError
from .pyside6_adapter import PySide6Adapter
from .pyqt6_adapter import PyQt6Adapter
from .pyside2_adapter import PySide2Adapter
from .pyqt5_adapter import PyQt5Adapter
from .kivy_adapter import KivyAdapter
from .tkinter_adapter import TkinterAdapter
from .headless_adapter import HeadlessAdapter


class FrameworkFactory:
    """Instantiates framework adapters based on preference or automatic detection."""

    _FRAMEWORK_REGISTRY = {
        "pyside6": PySide6Adapter,
        "pyqt6": PyQt6Adapter,
        "pyside2": PySide2Adapter,
        "pyqt5": PyQt5Adapter,
        "kivy": KivyAdapter,
        "tkinter": TkinterAdapter,
        "headless": HeadlessAdapter,
    }

    @classmethod
    def create(cls, name: Optional[str] = None) -> IUIFrameworkPort:
        if name:
            normalized = name.strip().lower()
            adapter_cls = cls._FRAMEWORK_REGISTRY.get(normalized)
            if not adapter_cls:
                raise FrameworkNotAvailableError(
                    name,
                    f"Supported frameworks: {', '.join(cls._FRAMEWORK_REGISTRY.keys())}"
                )
            adapter = adapter_cls()
            if not adapter.is_available():
                raise FrameworkNotAvailableError(adapter.framework_name)
            return adapter

        # Auto-detect in order of preference
        preference = [
            PySide6Adapter,
            PyQt6Adapter,
            PySide2Adapter,
            PyQt5Adapter,
            KivyAdapter,
            TkinterAdapter,
            HeadlessAdapter,
        ]
        for candidate_cls in preference:
            candidate = candidate_cls()
            if candidate.is_available():
                return candidate

        return HeadlessAdapter()

