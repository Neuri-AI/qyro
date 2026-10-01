"""
Headless Framework Adapter for CI, tests, and headless environments.
"""

from typing import Any, List, Optional
from qyro.application.ports.ui_framework import IUIFrameworkPort


class HeadlessApplication:
    """Mock GUI application instance for headless environments."""

    def __init__(self, argv: Optional[List[str]] = None) -> None:
        self.argv = argv or []

    def exec(self) -> int:
        return 0

    def exec_(self) -> int:
        return 0


class HeadlessAdapter(IUIFrameworkPort):
    """Fallback adapter when running in headless mode or without GUI libraries installed."""

    def __init__(self) -> None:
        super().__init__()
        self.applied_app_icon: Optional[str] = None
        self.applied_window_icons: dict = {}
        self.applied_window_titles: dict = {}

    @property
    def framework_name(self) -> str:
        return "Headless"

    def is_available(self) -> bool:
        return True

    def create_application(self, argv: Optional[List[str]] = None) -> Any:
        return HeadlessApplication(argv)

    def run(self) -> int:
        return 0

    def exit(self, code: int = 0) -> None:
        pass

    def set_application_icon(self, icon_path: str) -> bool:
        self.applied_app_icon = icon_path
        return True

    def set_window_icon(self, window: Any, icon_path: str) -> bool:
        self.applied_window_icons[window] = icon_path
        return True

    def set_window_title(self, window: Any, title: str) -> bool:
        self.applied_window_titles[window] = title
        return True
