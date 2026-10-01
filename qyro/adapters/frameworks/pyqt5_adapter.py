from .qt_base import BaseQtAdapter


class PyQt5Adapter(BaseQtAdapter):
    """PyQt5 toolkit adapter for Qt 5."""

    def __init__(self) -> None:
        qapp = None
        if self.is_available():
            from PyQt5.QtWidgets import QApplication
            qapp = QApplication
        super().__init__(qapp_class=qapp, is_qt6=False)

    @property
    def framework_name(self) -> str:
        return "PyQt5"

    def is_available(self) -> bool:
        try:
            import PyQt5.QtWidgets  # noqa: F401
            return True
        except ImportError:
            return False
