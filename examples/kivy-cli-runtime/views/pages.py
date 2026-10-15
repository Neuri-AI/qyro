"""Qyro Component views composed into the Kivy tab layout."""

from pathlib import Path

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from qyro import Component, EngineContainer

from components import (
    CounterCard, DevToolsButton, InfoCard, ProfileEditor, ProfilePreview,
    RuntimeInfoCard,
)
from store import store
from theme import tokens


class DemoView(BoxLayout, Component):
    """Base page: receives the application context as a prop, like the Qt demo."""

    def component_will_mount(self):
        self.orientation, self.spacing, self.padding = "vertical", dp(10), dp(16)
        self.app_context = self.props.get("context")
        self.title, self.detail = self.props["title"], self.props["detail"]

    def render(self):
        self.title_label = Label(text=self.title, bold=True, font_size="24sp",
                                 size_hint_y=None, height=dp(34), halign="left")
        self.detail_label = Label(text=self.detail, size_hint_y=None, height=dp(34),
                                  halign="left", valign="middle")
        self.title_label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.detail_label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.add_widget(self.title_label)
        self.add_widget(self.detail_label)

    def apply_theme(self, theme_name):
        palette = tokens(theme_name)
        self.title_label.color = palette["text"]
        self.detail_label.color = palette["muted"]
        for widget in self.children:
            apply_theme = getattr(widget, "apply_theme", None)
            if callable(apply_theme):
                apply_theme(theme_name)


class HelloView(DemoView):
    def component_did_mount(self):
        settings = self.app_settings
        self.add_widget(InfoCard(
            title="ApplicationContext + helpers",
            message=(
                f"App: {settings.get('app_name')} v{settings.get('version')}\n"
                f"Platform: {self.app_context.platform.value} | frozen: {self.is_frozen}"
            ),
        ))


class ComponentsView(DemoView):
    def component_did_mount(self):
        self.add_widget(InfoCard(
            title="Props directas",
            message="name='Ada Lovelace' · role='Arquitecta de software'",
        ))
        self.add_widget(InfoCard(
            title="Props por diccionario",
            message="props={'name': 'Linus Torvalds'} · role='Mantenedor'",
        ))


class ResourcesView(DemoView):
    def component_did_mount(self):
        greeting = Path(self.get_resource("text/greeting.txt")).read_text(encoding="utf-8")
        optional = Path(self.get_resource("themes/seasonal.kv", required=False))
        listed = sorted(
            path.name
            for path in self.app_context.container.resource_adapter.list_resources("text")
        )
        self.add_widget(InfoCard(
            title="get_resource + list_resources",
            message=(
                f"{greeting}\nOpcional existe: {optional.is_file()}\n"
                f"resources/text: {', '.join(listed)}"
            ),
        ))


class ContextView(DemoView):
    def component_did_mount(self):
        settings = self.app_settings
        self.add_widget(InfoCard(
            title="Contexto explícito y helpers",
            message=(
                f"Identifier: {self.app_context.metadata.identifier}\n"
                f"Theme: {settings.get('theme')} | frozen: {self.is_frozen}\n"
                "El contexto se inyecta aquí; helpers evitan prop drilling."
            ),
        ))
        self.runtime_card = RuntimeInfoCard()
        self.add_widget(self.runtime_card)

    def cleanup(self):
        self.runtime_card.component_will_unmount()


class ContainerView(DemoView):
    def component_did_mount(self):
        isolated = EngineContainer(
            framework_name="Headless", custom_root=Path(__file__).parents[1],
            enable_sentry=False,
        )
        metadata = isolated.load_settings_use_case.execute()
        self.add_widget(InfoCard(
            title="EngineContainer avanzado",
            message=(
                f"UI: {type(isolated.framework_adapter).__name__}\n"
                f"Resources: {type(isolated.resource_adapter).__name__}\n"
                f"Metadata Headless: {metadata.app_name}"
            ),
        ))


class PyduxView(DemoView):
    def component_did_mount(self):
        self.counter_card = CounterCard(title="CounterCard conectado a Pydux")
        self.add_widget(self.counter_card)
        inspector = getattr(store, "inspector", None)
        if inspector:
            self.devtools = DevToolsButton(inspector.base_url, size_hint_y=None, height=dp(42))
            self.add_widget(self.devtools)
        else:
            self.devtools = InfoCard(
                title="Pydux DevTools",
                message="Está desactivado cuando is_frozen() detecta la versión de producción.",
            )
            self.add_widget(self.devtools)

    def cleanup(self):
        self.counter_card.component_will_unmount()


class PayloadsView(DemoView):
    def component_did_mount(self):
        self.editor = ProfileEditor(title="Componente emisor")
        self.preview = ProfilePreview(title="Componente receptor")
        self.add_widget(self.editor)
        self.add_widget(self.preview)

    def cleanup(self):
        self.preview.component_will_unmount()
