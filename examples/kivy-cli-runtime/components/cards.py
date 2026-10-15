"""Theme-aware, prop-driven widgets used by the Kivy Qyro demo."""

import webbrowser

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

from pydux.adapters.qyro import Reactive
from qyro import Component

from store import (
    counter_slice, profile_slice, refresh_runtime_info, select_counter,
    select_profile, select_runtime_info, store,
)
from theme import tokens


class ThemedCard(BoxLayout):
    """A rounded Kivy card; Kivy's canvas is the equivalent of a QSS card."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._card_color = Color(*tokens("light")["surface"])
            self._card_background = RoundedRectangle(radius=[dp(12)])
        self.bind(pos=self._sync_background, size=self._sync_background)

    def _sync_background(self, *_):
        self._card_background.pos = self.pos
        self._card_background.size = self.size

    def apply_theme(self, theme_name):
        palette = tokens(theme_name)
        self._card_color.rgba = palette["surface"]
        for widget in self.children:
            apply_theme = getattr(widget, "apply_theme", None)
            if callable(apply_theme):
                apply_theme(theme_name)


class InfoCard(ThemedCard, Component):
    """A reusable visual component whose non-native keywords are Qyro props."""

    def component_will_mount(self):
        self.orientation = "vertical"
        self.spacing = dp(6)
        self.padding = dp(14)
        self.size_hint_y = None
        self.height = dp(106)
        self.title = self.props.get("title", "Información")
        self.message = self.props.get("message", "")

    def render(self):
        self.title_label = Label(text=self.title, bold=True, font_size="16sp",
                                 size_hint_y=None, height=dp(26), halign="left")
        self.message_label = Label(text=self.message, halign="left", valign="middle")
        self.title_label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.message_label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.add_widget(self.title_label)
        self.add_widget(self.message_label)
        self.apply_theme("light")

    def apply_theme(self, theme_name):
        super().apply_theme(theme_name)
        palette = tokens(theme_name)
        if hasattr(self, "title_label"):
            self.title_label.color = palette["accent"]
            self.message_label.color = palette["muted"]


class CounterCard(ThemedCard, Component, Reactive):
    def component_will_mount(self):
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.padding = dp(14)
        self.size_hint_y = None
        self.height = dp(172)
        self.title = self.props.get("title", "Contador")
        self.bind_selector(store, select_counter, self.update_count)

    def render(self):
        self.title_label = Label(text=self.title, bold=True, font_size="16sp",
                                 size_hint_y=None, height=dp(26), halign="left")
        self.value_label = Label(text="Preparando store…", font_size="18sp")
        controls = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(42))
        self.decrement = Button(text="−1")
        self.increment = Button(text="+1")
        self.decrement.bind(on_release=lambda *_: store.dispatch(counter_slice.actions.decrement()))
        self.increment.bind(on_release=lambda *_: store.dispatch(counter_slice.actions.increment()))
        controls.add_widget(self.decrement)
        controls.add_widget(self.increment)
        self.add_widget(self.title_label)
        self.add_widget(self.value_label)
        self.add_widget(controls)
        self.apply_theme("light")

    def update_count(self, text):
        if hasattr(self, "value_label"):
            self.value_label.text = text

    def component_did_mount(self):
        self.update_count(select_counter(store.get_state()))

    def apply_theme(self, theme_name):
        super().apply_theme(theme_name)
        palette = tokens(theme_name)
        if hasattr(self, "title_label"):
            self.title_label.color = palette["accent"]
            self.value_label.color = palette["text"]
            for button in (self.decrement, self.increment):
                button.background_color = palette["accent"]
                button.color = palette["accent_text"]


class ProfileEditor(ThemedCard, Component):
    def component_will_mount(self):
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.padding = dp(14)

    def render(self):
        self.title_label = Label(text=self.props.get("title", "Componente emisor"), bold=True,
                                 font_size="16sp", size_hint_y=None, height=dp(26), halign="left")
        self.name_input = TextInput(text="Grace Hopper", multiline=False, hint_text="Nombre")
        self.role_input = TextInput(text="Pionera de compiladores", multiline=False, hint_text="Rol")
        self.send = Button(text="Enviar payload", size_hint_y=None, height=dp(42))
        self.send.bind(on_release=self.send_profile)
        for widget in (self.title_label, self.name_input, self.role_input, self.send):
            self.add_widget(widget)
        self.apply_theme("light")

    def send_profile(self, *_):
        store.dispatch(profile_slice.actions.set_profile({
            "name": self.name_input.text.strip() or "Sin nombre",
            "role": self.role_input.text.strip() or "Sin rol",
        }))

    def apply_theme(self, theme_name):
        super().apply_theme(theme_name)
        palette = tokens(theme_name)
        if hasattr(self, "title_label"):
            self.title_label.color = palette["accent"]
            for field in (self.name_input, self.role_input):
                field.background_color = palette["input"]
                field.foreground_color = palette["text"]
                field.hint_text_color = palette["muted"]
                field.cursor_color = palette["accent"]
            self.send.background_color = palette["accent"]
            self.send.color = palette["accent_text"]


class ProfilePreview(ThemedCard, Component, Reactive):
    def component_will_mount(self):
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.padding = dp(14)
        self.bind_selector(store, select_profile, self.update_profile)

    def render(self):
        self.title_label = Label(text=self.props.get("title", "Componente receptor"), bold=True,
                                 font_size="16sp", size_hint_y=None, height=dp(26), halign="left")
        self.name_label = Label(text="Nombre: preparando…")
        self.role_label = Label(text="Rol: preparando…")
        for widget in (self.title_label, self.name_label, self.role_label):
            self.add_widget(widget)
        self.apply_theme("light")

    def update_profile(self, profile):
        if hasattr(self, "name_label"):
            self.name_label.text = f"Nombre: {profile['name']}"
            self.role_label.text = f"Rol: {profile['role']}"

    def component_did_mount(self):
        self.update_profile(select_profile(store.get_state()))

    def apply_theme(self, theme_name):
        super().apply_theme(theme_name)
        palette = tokens(theme_name)
        if hasattr(self, "title_label"):
            self.title_label.color = palette["accent"]
            self.name_label.color = palette["text"]
            self.role_label.color = palette["muted"]


class RuntimeInfoCard(InfoCard, Reactive):
    """Shows data obtained by Qyro helpers after it has crossed Pydux."""

    def component_will_mount(self):
        super().component_will_mount()
        self.title = "Runtime leído con helpers Qyro"
        self.message = "Aplicación: preparando…"
        self.bind_selector(store, select_runtime_info, self.update_runtime)

    def component_did_mount(self):
        store.dispatch(refresh_runtime_info())

    def update_runtime(self, runtime):
        if hasattr(self, "message_label"):
            mode = "frozen" if runtime["is_frozen"] else "source"
            self.message_label.text = (
                f"Aplicación: {runtime['app_name']}\n"
                f"Modo por is_frozen(): {mode}\n"
                f"Tema desde settings: {runtime['theme']}"
            )


class DevToolsButton(Button):
    """Opens the optional local Pydux inspector from within the demo."""

    def __init__(self, inspector_url, **kwargs):
        super().__init__(**kwargs)
        self.inspector_url = inspector_url
        self.text = f"Abrir Pydux DevTools ({inspector_url})"
        self.bind(on_release=lambda *_: webbrowser.open(self.inspector_url))

    def apply_theme(self, theme_name):
        palette = tokens(theme_name)
        self.background_color = palette["accent"]
        self.color = palette["accent_text"]
