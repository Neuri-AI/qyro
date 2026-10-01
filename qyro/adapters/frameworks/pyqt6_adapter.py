"""
PyQt6 Adapter.
Riverbank PyQt6 binding implementation for Qyro.
"""

from typing import Any, List, Optional
from .qt_base import BaseQtAdapter


class PyQt6Adapter(BaseQtAdapter):
    """PyQt6 toolkit adapter."""

    def __init__(self) -> None:
        qapp = None
        if self.is_available():
            from PyQt6.QtWidgets import QApplication
            qapp = QApplication
        super().__init__(qapp_class=qapp, is_qt6=True)

    @property
    def framework_name(self) -> str:
        return "PyQt6"

    def is_available(self) -> bool:
        try:
            import PyQt6.QtWidgets  # noqa: F401
            return True
        except ImportError:
            return False

    def create_application(self, argv: Optional[List[str]] = None) -> Any:
        if not self._qapp_class and self.is_available():
            from PyQt6.QtWidgets import QApplication
            self._qapp_class = QApplication
        return super().create_application(argv)
