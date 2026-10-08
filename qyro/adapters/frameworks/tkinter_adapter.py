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
            self._activate_window()
            self._app.mainloop()
        return 0

    def _activate_window(self) -> None:
        """Present the first Tk window when Qyro enters its event loop.

        ``qyro start`` is launched from a terminal, and macOS does not always
        foreground a Tk process in that case.  These are no-ops on toolkits or
        test doubles that do not implement the corresponding Tk methods.
        """
        if not self._app:
            return
        try:
            self._app.update_idletasks()
            self._app.deiconify()
            self._app.lift()
            self._app.focus_force()
            after_idle = getattr(self._app, "after_idle", None)
            if callable(after_idle):
                after_idle(self._app.lift)
        except Exception:
            # Focus can be declined by the platform window manager; the app
            # remains usable and should still enter its normal main loop.
            pass

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
