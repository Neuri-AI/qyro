"""CLI-generated Tkinter project extended with Qyro Engine demos."""

import tkinter as tk

from qyro import ApplicationContext, Component
from store import store
from theme import tokens
from views import ComponentsView, ContainerView, ContextView, HelloView, PayloadsView, PyduxView, ResourcesView


class ThemeLabel(tk.Label):
    """A clickable label whose colors are not overridden by macOS Aqua."""

    def __init__(self, parent, command, **kwargs):
        super().__init__(parent, cursor="hand2", **kwargs)
        self.bind("<Button-1>", lambda _event: command())


class QyroTkinterDemos(tk.Tk, Component, ApplicationContext):
    def component_will_mount(self):
        window = self.app_settings.get("window", {})
        self.geometry(f"{window.get('width', 980)}x{window.get('height', 680)}")
        self.minsize(760, 520)
        self.title(self.app_settings.get("app_name", "Qyro Tkinter Demos"))
        self.current_theme = self.app_settings.get("theme", "light")
        self._shutdown_complete = False
        self.protocol("WM_DELETE_WINDOW", self.close_application)
        # qyro start launches Python as a child process. Ask macOS to bring
        # this Tk window forward once its native window exists.
        self.after_idle(self._activate_window)

    def _activate_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(120, lambda: self.attributes("-topmost", False))

    def render(self):
        root = tk.Frame(self, padx=12, pady=12)
        root.pack(fill="both", expand=True)
        self.header = tk.Frame(root, padx=18, pady=16)
        self.header.pack(fill="x")
        self.header_title = tk.Label(self.header, text="Qyro Engine · Tkinter demos", anchor="w", font=("TkDefaultFont", 20, "bold"))
        self.header_title.pack(side="left", fill="x", expand=True)
        self.theme_button = ThemeLabel(self.header, self.toggle_theme, padx=18, pady=9)
        self.theme_button.pack(side="right")
        self.tab_bar = tk.Frame(root, padx=4, pady=4)
        self.tab_bar.pack(fill="x", pady=(12, 0))
        self.tab_content = tk.Frame(root)
        self.tab_content.pack(fill="both", expand=True)
        specs = (
            ("Hello", HelloView, "Hello, World!", "Contexto, metadata y helpers."),
            ("Components", ComponentsView, "Componentes y props", "Componentes Tkinter reutilizables."),
            ("Resources", ResourcesView, "Recursos", "Resolución source/frozen."),
            ("Context", ContextView, "Settings", "Contexto explícito y helpers."),
            ("Container", ContainerView, "Container", "API Headless avanzada."),
            ("Pydux", PyduxView, "Pydux", "Estado, selector y DevTools."),
            ("Payloads", PayloadsView, "Payloads", "Emisor y receptor desacoplados."),
        )
        self.views = []
        self.tab_buttons = []
        self.selected_tab = None
        for index, (tab_text, view_type, title, detail) in enumerate(specs):
            button = ThemeLabel(self.tab_bar, lambda i=index: self.select_tab(i),
                                text=tab_text, padx=16, pady=10)
            button.pack(side="left", fill="x", expand=True, padx=2)
            self.tab_buttons.append(button)
            view = view_type(self.tab_content, context=self, title=title, detail=detail)
            view.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.views.append(view)
        self.select_tab(0)
        self.apply_theme()

    def apply_theme(self):
        palette = tokens(self.current_theme)
        self.configure(bg=palette["window"])
        self.header.configure(bg=palette["surface"])
        self.header_title.configure(bg=palette["surface"], fg=palette["text"])
        self.theme_button.configure(
            text="Usar tema Dark" if self.current_theme == "light" else "Usar tema Light",
            bg=palette["accent"], fg=palette["accent_text"],
        )
        self.tab_bar.configure(bg=palette["surface_alt"])
        self.tab_content.configure(bg=palette["window"])
        for index, button in enumerate(self.tab_buttons):
            selected = index == self.selected_tab
            button.configure(
                bg=palette["accent"] if selected else palette["surface_alt"],
                fg=palette["accent_text"] if selected else palette["text"],
            )
        for view in self.views:
            view.apply_theme(self.current_theme)

    def select_tab(self, index):
        """Switch views directly; unlike ttk.Notebook this is theme-independent."""
        self.selected_tab = index
        self.views[index].tkraise()
        if hasattr(self, "current_theme"):
            self.apply_theme()

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()

    def close_application(self):
        self._shutdown()
        self.destroy()

    def _shutdown(self):
        if self._shutdown_complete:
            return
        self._shutdown_complete = True
        for view in getattr(self, "views", []):
            cleanup = getattr(view, "cleanup", None)
            if callable(cleanup):
                cleanup()
        inspector = getattr(store, "inspector", None)
        if inspector:
            inspector.stop()


if __name__ == "__main__":
    QyroTkinterDemos().mainloop()
