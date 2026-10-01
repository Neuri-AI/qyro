from typing import Any, List, Optional
from .base import BaseUIFrameworkAdapter

class TkinterAdapter(BaseUIFrameworkAdapter):
    """Tkinter builtin toolkit adapter (no external dependencies required)."""

    @property
    def framework_name(self) -> str:
        return "Tkinter"

    def is_available(self) -> bool:
        try:
            import tkinter  # noqa: F401
            return True
        except ImportError:
            return False

    def create_application(self, argv: Optional[List[str]] = None) -> Any:
        try:
            import tkinter as tk
            if getattr(tk, "_default_root", None):
                self._app = getattr(tk, "_default_root")
                return self._app
        except Exception:
            pass
        return None

    def run(self) -> int:
        if not self._app:
            try:
                import tkinter as tk
                self._app = getattr(tk, "_default_root", None)
                if not self._app:
                    self._app = tk.Tk()
            except Exception:
                self._app = None
        self._is_running = True
        if self._app and hasattr(self._app, "mainloop"):
            self._app.mainloop()
        return 0

    def exit(self, code: int = 0) -> None:
        if self._app and hasattr(self._app, "destroy"):
            self._app.destroy()
        self._is_running = False

    def set_application_icon(self, icon_path: str) -> bool:
        if not self._app:
            try:
                import tkinter as tk
                self._app = getattr(tk, "_default_root", None)
            except Exception:
                pass
        if not self._app:
            return False
        return self.set_window_icon(self._app, icon_path)

    def set_window_icon(self, window: Any, icon_path: str) -> bool:
        if not window:
            return False
        try:
            import tkinter as tk
            if icon_path.endswith(".ico") and hasattr(window, "iconbitmap"):
                window.iconbitmap(icon_path)
                return True
            elif hasattr(window, "iconphoto"):
                photo = tk.PhotoImage(file=icon_path)
                window.iconphoto(True, photo)
                # Keep reference on window to prevent Tkinter garbage collection
                setattr(window, "_qyro_icon_photo", photo)
                return True
        except Exception:
            pass
        return False

    def set_window_title(self, window: Any, title: str) -> bool:
        if window and hasattr(window, "title") and callable(window.title):
            window.title(title)
            return True
        return False