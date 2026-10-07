"""Page components loaded by the Tkinter notebook."""

from pathlib import Path
import tkinter as tk

from qyro import Component, EngineContainer
from components import CounterCard, DevToolsButton, InfoCard, ProfileEditor, ProfilePreview, RuntimeInfoCard
from store import store
from theme import tokens


class DemoView(tk.Frame, Component):
    def component_will_mount(self):
        self.app_context = self.props.get("context")
        self.title, self.detail = self.props["title"], self.props["detail"]
        self.configure(padx=18, pady=16)

    def render(self):
        self.title_label = tk.Label(self, text=self.title, anchor="w", font=("TkDefaultFont", 22, "bold"))
        self.detail_label = tk.Label(self, text=self.detail, anchor="w", justify="left")
        self.title_label.pack(fill="x")
        self.detail_label.pack(fill="x", pady=(5, 14))

    def add_card(self, card):
        card.pack(fill="x", pady=(0, 12))
        return card

    def apply_theme(self, theme_name):
        palette = tokens(theme_name)
        self.configure(bg=palette["window"])
        self.title_label.configure(bg=palette["window"], fg=palette["text"])
        self.detail_label.configure(bg=palette["window"], fg=palette["muted"])
        for child in self.winfo_children():
            apply_theme = getattr(child, "apply_theme", None)
            if callable(apply_theme):
                apply_theme(theme_name)


class HelloView(DemoView):
    def component_did_mount(self):
        settings = self.app_settings
        self.add_card(InfoCard(self, title="ApplicationContext + helpers", message=(
            f"App: {settings.get('app_name')} v{settings.get('version')}\n"
            f"Platform: {self.app_context.platform.value} | frozen: {self.is_frozen}")))


class ComponentsView(DemoView):
    def component_did_mount(self):
        self.add_card(InfoCard(self, title="Props directas", message="name='Ada Lovelace' · role='Arquitecta de software'"))
        self.add_card(InfoCard(self, title="Props por diccionario", message="props={'name': 'Linus Torvalds'} · role='Mantenedor'"))


class ResourcesView(DemoView):
    def component_did_mount(self):
        greeting = Path(self.get_resource("text/greeting.txt")).read_text(encoding="utf-8")
        optional = Path(self.get_resource("themes/seasonal.tcl", required=False))
        listed = sorted(path.name for path in self.app_context.container.resource_adapter.list_resources("text"))
        self.add_card(InfoCard(self, title="get_resource + list_resources", message=(
            f"{greeting}\nOpcional existe: {optional.is_file()}\nresources/text: {', '.join(listed)}")))


class ContextView(DemoView):
    def component_did_mount(self):
        settings = self.app_settings
        self.add_card(InfoCard(self, title="Contexto explícito y helpers", message=(
            f"Identifier: {self.app_context.metadata.identifier}\nTheme: {settings.get('theme')} | frozen: {self.is_frozen}\n"
            "El contexto se inyecta aquí; helpers evitan prop drilling.")))
        self.runtime_card = self.add_card(RuntimeInfoCard(self))

    def cleanup(self): self.runtime_card.component_will_unmount()


class ContainerView(DemoView):
    def component_did_mount(self):
        isolated = EngineContainer(framework_name="Headless", custom_root=Path(__file__).parents[1], enable_sentry=False)
        metadata = isolated.load_settings_use_case.execute()
        self.add_card(InfoCard(self, title="EngineContainer avanzado", message=(
            f"UI: {type(isolated.framework_adapter).__name__}\nResources: {type(isolated.resource_adapter).__name__}\n"
            f"Metadata Headless: {metadata.app_name}")))


class PyduxView(DemoView):
    def component_did_mount(self):
        self.counter_card = self.add_card(CounterCard(self, title="CounterCard conectado a Pydux"))
        inspector = getattr(store, "inspector", None)
        self.devtools = self.add_card(DevToolsButton(self, inspector.base_url) if inspector else InfoCard(
            self, title="Pydux DevTools", message="Está desactivado cuando is_frozen() detecta producción."))

    def cleanup(self): self.counter_card.component_will_unmount()


class PayloadsView(DemoView):
    def component_did_mount(self):
        self.editor = self.add_card(ProfileEditor(self, title="Componente emisor"))
        self.preview = self.add_card(ProfilePreview(self, title="Componente receptor"))

    def cleanup(self): self.preview.component_will_unmount()
