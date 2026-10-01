"""
UI Framework Port Contract.
Abstractions for GUI framework lifecycles (PySide6, PyQt6, PySide2, PyQt5, Kivy, Tkinter).
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional


class IUIFrameworkPort(ABC):
    """Abstract port for GUI toolkit lifecycle management."""

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Name of the framework (e.g. 'PySide6', 'PyQt6', 'Kivy', 'Tkinter')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the underlying GUI library can be imported."""
        pass

    @abstractmethod
    def create_application(self, argv: Optional[List[str]] = None) -> Any:
        """Instantiates or gets the primary application singleton (e.g. QApplication)."""
        pass

    @abstractmethod
    def run(self) -> int:
        """Starts the framework's main event loop. Returns exit status code."""
        pass

    @abstractmethod
    def exit(self, code: int = 0) -> None:
        """Terminates the framework event loop."""
        pass

    def set_application_icon(self, icon_path: str) -> bool:
        """Sets the application-level icon. Returns True if successfully applied."""
        return False

    def set_window_icon(self, window: Any, icon_path: str) -> bool:
        """Sets the icon on a specific window instance. Returns True if applied."""
        return False

    def set_window_title(self, window: Any, title: str) -> bool:
        """Sets the title of a specific window instance. Returns True if applied."""
        return False
