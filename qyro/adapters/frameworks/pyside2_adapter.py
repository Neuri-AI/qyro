"""
PySide2 and PyQt5 Legacy Adapters for Qt 5.
"""

from .qt_base import BaseQtAdapter


class PySide2Adapter(BaseQtAdapter):
    """PySide2 toolkit adapter for Qt 5."""

    def __init__(self) -> None:
        qapp = None
        if self.is_available():
            from PySide2.QtWidgets import QApplication
            qapp = QApplication
        super().__init__(qapp_class=qapp, is_qt6=False)

    @property
    def framework_name(self) -> str:
        return "PySide2"

    def is_available(self) -> bool:
        try:
            import PySide2.QtWidgets  # noqa: F401
            return True
        except ImportError:
            return False

