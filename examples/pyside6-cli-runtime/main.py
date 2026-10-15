"""CLI-generated PySide6 project that composes its page widgets from views."""
import sys

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QTabWidget,
    QVBoxLayout, QWidget,
)
from qyro import ApplicationContext, Component

from store import store
from views import (
    ComponentsView,
    ContainerView,
    ContextView,
    HelloView,
    PayloadsView,
    PyduxView,
    ResourcesView,
)


class QyroPyside6Demos(QMainWindow, Component, ApplicationContext):
    """Root application: it creates the layout and loads view widgets."""

    def component_will_mount(self):
        window = self.app_settings.get("window", {})
        self.resize(window.get("width", 860), window.get("height", 580))
        self.current_theme = self.app_settings.get("theme", "light")

    def render(self):
        shell = QWidget(self, objectName="appShell")
        shell_layout = QVBoxLayout(shell, spacing=14)
        shell_layout.setContentsMargins(20, 18, 20, 18)

        header = QFrame(shell, objectName="appHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)

        copy_layout = QVBoxLayout(spacing=4) # spacing opcional para separar título y subtítulo
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.addWidget(QLabel("Qyro Engine Lab", objectName="appTitle"))
        copy_layout.addWidget(
            QLabel("PySide6 · Components · Resources · Pydux", objectName="appSubtitle")
        )

        self.theme_toggle = QPushButton(header, objectName="themeToggle", clicked=self.toggle_theme)

        header_layout.addLayout(copy_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.theme_toggle)

        self.tabs = QTabWidget(shell)
        shell_layout.addWidget(header)
        shell_layout.addWidget(self.tabs)
        self.setCentralWidget(shell)

        page_specs = (
            ("Hello", HelloView, "Hello, World!", "La estructura se creó con qyro init."),
            ("Components", ComponentsView, "Componentes y props", "Los keywords no nativos pasan a props; no vuelven reactivo al componente."),
            ("Resources", ResourcesView, "Recursos source/frozen", "Qyro resuelve rutas sin depender del directorio actual."),
            ("Context", ContextView, "ApplicationContext y settings", "Los settings son configuración de arranque; no son estado mutable de UI."),
            ("Container", ContainerView, "API profunda: EngineContainer", "El contenedor Headless sirve para scripts y pruebas, sin crear otra QApplication."),
            ("Pydux", PyduxView, "Estado compartido con Pydux", "CounterCard recibe title por props y se conecta por sí mismo al selector de Pydux."),
            ("Payloads", PayloadsView, "Payloads entre componentes", "ProfileEditor despacha un payload y ProfilePreview se actualiza por el selector, sin una referencia directa entre ambos."),
        )
        self.views = []
        for tab_title, view_type, title, detail in page_specs:
            view = view_type(
                parent=self.tabs, context=self, title=title, detail=detail
            )
            self.views.append(view)
            self.tabs.addTab(view, tab_title)
        self.apply_theme()

    def apply_theme(self):
        self.set_styles(self.get_resource(f"themes/{self.current_theme}.qss"))
        next_theme = "Dark" if self.current_theme == "light" else "Light"
        self.theme_toggle.setText(f"Usar tema {next_theme}")

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()

    def closeEvent(self, event):
        for view in getattr(self, "views", []):
            cleanup = getattr(view, "cleanup", None)
            if callable(cleanup):
                cleanup()
        inspector = getattr(store, "inspector", None)
        if inspector:
            inspector.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    window = QyroPyside6Demos()
    window.show()
    sys.exit(window.run())
