"""Reusable Tkinter components for the Qyro feature demos."""

import tkinter as tk
import webbrowser

from pydux.adapters.qyro import Reactive
from qyro import Component

from store import (counter_slice, profile_slice, refresh_runtime_info, select_counter,
                   select_profile, select_runtime_info, store)
from theme import tokens


class ThemedCard(tk.Frame):
    def apply_theme(self, theme_name):
        palette = tokens(theme_name)
        self.configure(bg=palette["surface"], highlightbackground=palette["surface_alt"])
        for child in self.winfo_children():
            apply_theme = getattr(child, "apply_theme", None)
            if callable(apply_theme):
                apply_theme(theme_name)


class InfoCard(ThemedCard, Component):
    def component_will_mount(self):
        self.title = self.props.get("title", "Información")
        self.message = self.props.get("message", "")
        self.configure(padx=18, pady=14, bd=0, highlightthickness=1)

    def render(self):
        self.title_label = tk.Label(self, text=self.title, anchor="w", font=("TkDefaultFont", 15, "bold"))
        self.message_label = tk.Label(self, text=self.message, anchor="w", justify="left", wraplength=760)
        self.title_label.pack(fill="x")
        self.message_label.pack(fill="x", pady=(8, 0))
        self.apply_theme("light")

    def apply_theme(self, theme_name):
        super().apply_theme(theme_name)
        palette = tokens(theme_name)
        if hasattr(self, "title_label"):
            self.title_label.configure(bg=palette["surface"], fg=palette["accent"])
            self.message_label.configure(bg=palette["surface"], fg=palette["muted"])


class CounterCard(ThemedCard, Component, Reactive):
    def component_will_mount(self):
        self.title = self.props.get("title", "Contador")
        self.configure(padx=18, pady=14, bd=0, highlightthickness=1)
        self.bind_selector(store, select_counter, self.update_count)

    def render(self):
        self.title_label = tk.Label(self, text=self.title, anchor="w", font=("TkDefaultFont", 15, "bold"))
        self.value_label = tk.Label(self, text="Preparando store…", anchor="w", font=("TkDefaultFont", 13))
        controls = tk.Frame(self)
        self.minus = tk.Button(controls, text="−1", command=lambda: store.dispatch(counter_slice.actions.decrement()))
        self.plus = tk.Button(controls, text="+1", command=lambda: store.dispatch(counter_slice.actions.increment()))
        self.title_label.pack(fill="x")
        self.value_label.pack(fill="x", pady=8)
        controls.pack(fill="x")
        self.minus.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.plus.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.controls = controls
        self.apply_theme("light")

    def component_did_mount(self):
        self.update_count(select_counter(store.get_state()))

    def update_count(self, text):
        if hasattr(self, "value_label"):
            self.value_label.configure(text=text)

    def apply_theme(self, theme_name):
        super().apply_theme(theme_name)
        palette = tokens(theme_name)
        if hasattr(self, "title_label"):
            self.title_label.configure(bg=palette["surface"], fg=palette["accent"])
            self.value_label.configure(bg=palette["surface"], fg=palette["text"])
            self.controls.configure(bg=palette["surface"])
            for button in (self.minus, self.plus):
                button.configure(bg=palette["accent"], fg=palette["accent_text"], activebackground=palette["accent"], relief="flat")


class ProfileEditor(ThemedCard, Component):
    def component_will_mount(self):
        self.configure(padx=18, pady=14, bd=0, highlightthickness=1)

    def render(self):
        self.title_label = tk.Label(self, text=self.props.get("title", "Componente emisor"), anchor="w", font=("TkDefaultFont", 15, "bold"))
        self.name_input = tk.Entry(self)
        self.role_input = tk.Entry(self)
        self.name_input.insert(0, "Grace Hopper")
        self.role_input.insert(0, "Pionera de compiladores")
        self.send = tk.Button(self, text="Enviar payload", command=self.send_profile)
        for widget in (self.title_label, self.name_input, self.role_input, self.send):
            widget.pack(fill="x", pady=(0, 8))
        self.apply_theme("light")

    def send_profile(self):
        store.dispatch(profile_slice.actions.set_profile({
            "name": self.name_input.get().strip() or "Sin nombre",
            "role": self.role_input.get().strip() or "Sin rol",
        }))

    def apply_theme(self, theme_name):
        super().apply_theme(theme_name)
        palette = tokens(theme_name)
        if hasattr(self, "title_label"):
            self.title_label.configure(bg=palette["surface"], fg=palette["accent"])
            for field in (self.name_input, self.role_input):
                field.configure(bg=palette["input"], fg=palette["text"], insertbackground=palette["accent"])
            self.send.configure(bg=palette["accent"], fg=palette["accent_text"], activebackground=palette["accent"], relief="flat")


class ProfilePreview(InfoCard, Reactive):
    def component_will_mount(self):
        super().component_will_mount()
        self.title = self.props.get("title", "Componente receptor")
        self.message = "Nombre: preparando…"
        self.bind_selector(store, select_profile, self.update_profile)

    def component_did_mount(self):
        self.update_profile(select_profile(store.get_state()))

    def update_profile(self, profile):
        if hasattr(self, "message_label"):
            self.message_label.configure(text=f"Nombre: {profile['name']}\nRol: {profile['role']}")


class RuntimeInfoCard(InfoCard, Reactive):
    def component_will_mount(self):
        super().component_will_mount()
        self.title, self.message = "Runtime leído con helpers Qyro", "Aplicación: preparando…"
        self.bind_selector(store, select_runtime_info, self.update_runtime)

    def component_did_mount(self):
        store.dispatch(refresh_runtime_info())

    def update_runtime(self, runtime):
        if hasattr(self, "message_label"):
            mode = "frozen" if runtime["is_frozen"] else "source"
            self.message_label.configure(text=f"Aplicación: {runtime['app_name']}\nModo por is_frozen(): {mode}\nTema desde settings: {runtime['theme']}")


class DevToolsButton(tk.Button):
    def __init__(self, parent, inspector_url):
        super().__init__(parent, text=f"Abrir Pydux DevTools ({inspector_url})", command=lambda: webbrowser.open(inspector_url))

    def apply_theme(self, theme_name):
        palette = tokens(theme_name)
        self.configure(bg=palette["accent"], fg=palette["accent_text"], activebackground=palette["accent"], relief="flat")
