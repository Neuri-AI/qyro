"""
Kivy and Tkinter Framework Adapters for Qyro.
Supports cross-platform desktop/mobile (Kivy) and lightweight builtin (Tkinter) runtimes.
"""

import sys
from typing import Any, List, Optional
from .base import BaseUIFrameworkAdapter


class KivyAdapter(BaseUIFrameworkAdapter):
    """Kivy toolkit adapter for multi-touch and mobile/desktop apps."""

    @property
    def framework_name(self) -> str:
        return "Kivy"

    def is_available(self) -> bool:
        try:
            import kivy  # noqa: F401
            return True
        except ImportError:
            return False

    def create_application(self, argv: Optional[List[str]] = None) -> Any:
        try:
            from kivy.app import App
            running = App.get_running_app()
            if running:
                self._app = running
                return self._app
        except Exception:
            pass
        return None

    def run(self) -> int:
        if not self._app:
            try:
                from kivy.app import App
                self._app = App.get_running_app()
            except Exception:
                pass
        if not self._app:
            from kivy.app import App

            class GenericKivyApp(App):
                pass

            self._app = GenericKivyApp()

        self._is_running = True
        self._app.run()
        return 0

    def exit(self, code: int = 0) -> None:
        if self._app and hasattr(self._app, "stop"):
            self._app.stop()
        self._is_running = False

    def set_application_icon(self, icon_path: str) -> bool:
        if self._app and hasattr(self._app, "icon"):
            self._app.icon = icon_path
            return True
        return False

    def set_window_icon(self, window: Any, icon_path: str) -> bool:
        if window and hasattr(window, "icon"):
            window.icon = icon_path
            return True
        return self.set_application_icon(icon_path)

    def set_window_title(self, window: Any, title: str) -> bool:
        if window and hasattr(window, "title"):
            window.title = title
            return True
        if self._app and hasattr(self._app, "title"):
            self._app.title = title
            return True
        return False