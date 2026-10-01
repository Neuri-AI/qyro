"""
Base Qt Adapter for PySide and PyQt bindings.
Encapsulates common QApplication creation, high-DPI attributes, and event loop execution.
"""

import sys
from typing import Any, List, Optional
from .base import BaseUIFrameworkAdapter


class BaseQtAdapter(BaseUIFrameworkAdapter):
    """Shared implementation details across PyQt and PySide versions."""

    def __init__(self, qapp_class: Any, is_qt6: bool = True) -> None:
        super().__init__()
        self._qapp_class = qapp_class
        self._is_qt6 = is_qt6

    def create_application(self, argv: Optional[List[str]] = None) -> Any:
        if self._qapp_class.instance():
            self._app = self._qapp_class.instance()
            return self._app

        args = argv if argv is not None else sys.argv
        self._app = self._qapp_class(args)
        return self._app

    def run(self) -> int:
        if not self._app:
            self.create_application()

        self._is_running = True
        # Qt 6 uses app.exec(), Qt 5 used app.exec_()
        if hasattr(self._app, "exec"):
            return self._app.exec()
        return self._app.exec_()

    def exit(self, code: int = 0) -> None:
        if self._app:
            self._app.exit(code)
        self._is_running = False

    @property
    def binding_package(self) -> str:
        """Determines the exact Qt package name associated with this adapter instance."""
        if self._qapp_class and hasattr(self._qapp_class, "__module__"):
            return self._qapp_class.__module__.split(".")[0]
        return self.framework_name

    def _create_qicon(self, icon_path: str, target: Optional[Any] = None) -> Optional[Any]:
        """
        Dynamically imports QIcon strictly from the adapter's matching Qt binding.
        Avoids cross-importing other installed Qt bindings (e.g. PySide6 when running PyQt5),
        which causes macOS duplicate symbol warnings, QPixmap crashes, and SIGABRT.
        """
        pkg = None
        if target is not None:
            for cls in getattr(type(target), "__mro__", []):
                mod = getattr(cls, "__module__", "")
                if mod:
                    root = mod.split(".")[0]
                    if root in ("PyQt5", "PySide6", "PyQt6", "PySide2"):
                        pkg = root
                        break

        if not pkg:
            pkg = self.binding_package

        if pkg:
            try:
                mod = __import__(f"{pkg}.QtGui", fromlist=["QIcon"])
                QIcon = getattr(mod, "QIcon", None)
                if QIcon:
                    return QIcon(icon_path)
            except Exception:
                pass
        return None

    def set_application_icon(self, icon_path: str) -> bool:
        if not self._app:
            return False
        qicon = self._create_qicon(icon_path, target=self._app)
        if qicon and hasattr(self._app, "setWindowIcon"):
            self._app.setWindowIcon(qicon)
            return True
        return False

    def set_window_icon(self, window: Any, icon_path: str) -> bool:
        if not window:
            return False
        qicon = self._create_qicon(icon_path, target=window)
        if qicon and hasattr(window, "setWindowIcon"):
            try:
                window.setWindowIcon(qicon)
                return True
            except (RuntimeError, Exception):
                return False
        return False

    def set_window_title(self, window: Any, title: str) -> bool:
        if window and hasattr(window, "setWindowTitle"):
            try:
                window.setWindowTitle(title)
                return True
            except (RuntimeError, Exception):
                return False
        return False
