"""CLI-generated Kivy project extended with Qyro Engine demos."""

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem

from qyro import ApplicationContext, Component
from store import store
from theme import tokens
from views import (
    ComponentsView, ContainerView, ContextView, HelloView, PayloadsView,
    PyduxView, ResourcesView,
)


class QyroKivyDemos(App, Component, ApplicationContext):
    def component_will_mount(self):
        window = self.app_settings.get("window", {})
        if Window:
            Window.size = (window.get("width", 900), window.get("height", 620))
            Window.minimum_size = (720, 500)
            # Register a native close listener. On macOS/SDL2 this makes Kivy
            # leave its loop through App.stop(), so on_stop can dispose Pydux.
            Window.bind(on_request_close=self._request_close)
        self.current_theme = self.app_settings.get("theme", "light")
        self._shutdown_complete = False

    def render(self):
        if hasattr(self, "root_widget"):
            return self.root_widget

        root = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        controls = BoxLayout(size_hint_y=None, height=dp(74), spacing=dp(8), padding=dp(12))
        with controls.canvas.before:
            self.header_color = Color(*tokens("light")["surface"])
            self.header_background = Rectangle()
        controls.bind(pos=self._sync_header, size=self._sync_header)
        self.header_title = Label(
            text="Qyro Engine · Kivy demos", font_size="20sp", bold=True,
            halign="left", valign="middle",
        )
        self.header_title.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        controls.add_widget(self.header_title)
        self.theme_button = Button()
        self.theme_button.bind(on_release=lambda *_: self.toggle_theme())
        controls.add_widget(self.theme_button)
        root.add_widget(controls)

        tabs = TabbedPanel(do_default_tab=False, tab_height=dp(40))
        self.tabs = tabs
        self.tab_items = []
        tabs.bind(current_tab=lambda *_: self.apply_tab_theme())
        specs = (
            ("Hello", HelloView, "Hello, World!", "Contexto, metadata y helpers."),
            ("Components", ComponentsView, "Componentes y props", "Componentes Kivy reutilizables."),
            ("Resources", ResourcesView, "Recursos", "Resolución source/frozen."),
            ("Context", ContextView, "Settings", "Contexto explícito y helpers."),
            ("Container", ContainerView, "Container", "API Headless avanzada."),
            ("Pydux", PyduxView, "Pydux", "Estado, selector y DevTools."),
            ("Payloads", PayloadsView, "Payloads", "Emisor y receptor desacoplados."),
        )
        self.views = []
        for tab_text, view_type, title, detail in specs:
            tab = TabbedPanelItem(
                text=tab_text, background_normal="", background_down="",
            )
            self.tab_items.append(tab)
            view = view_type(context=self, title=title, detail=detail)
            self.views.append(view)
            tab.add_widget(view)
            tabs.add_widget(tab)
        # TabbedPanel otherwise keeps an internal blank default header as the
        # current tab, leaving every visible tab styled as inactive.
        tabs.switch_to(self.tab_items[0])
        root.add_widget(tabs)
        self.root_widget = root
        self.apply_theme()
        return root

    def apply_theme(self):
        palette = tokens(self.current_theme)
        if Window:
            Window.clearcolor = palette["window"]
        self.header_color.rgba = palette["surface"]
        self.header_title.color = palette["text"]
        self.theme_button.text = (
            "Usar tema Dark" if self.current_theme == "light" else "Usar tema Light"
        )
        self.theme_button.background_color = palette["accent"]
        self.theme_button.color = palette["accent_text"]
        # TabbedPanel ships with a dark atlas texture even when the window is
        # light. Remove that image and paint the content area with our palette.
        self.tabs.background_image = ""
        self.tabs.background_color = palette["surface"]
        self.apply_tab_theme()
        for view in self.views:
            view.apply_theme(self.current_theme)

    def apply_tab_theme(self):
        """Give the active Kivy tab the same clear state as the Qt demo."""
        palette = tokens(self.current_theme)
        active = self.tabs.current_tab
        for tab in self.tab_items:
            selected = tab is active
            tab.background_color = palette["accent"] if selected else palette["surface_alt"]
            tab.color = palette["accent_text"] if selected else palette["text"]

    def _sync_header(self, widget, *_):
        self.header_background.pos = widget.pos
        self.header_background.size = widget.size

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()

    def build(self):
        return self.render()

    def on_stop(self):
        self._shutdown()

    def _request_close(self, *_):
        """Route native window close through Kivy's orderly app shutdown."""
        self.stop()
        return True

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
    QyroKivyDemos().run()
