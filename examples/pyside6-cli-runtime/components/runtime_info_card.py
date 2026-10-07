from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from pydux.adapters.qyro import Reactive
from qyro import Component

from store import refresh_runtime_info, select_runtime_info, store
from .user_card import UserCard


class RuntimeInfoCard(QFrame, Component, Reactive):
    """Displays Qyro helper data after moving it through the Pydux store."""

    STYLES = UserCard.STYLES

    def component_will_mount(self):
        self.bind_selector(store, select_runtime_info, self.update_runtime)

    def render(self):
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        title = QLabel("Runtime leído con helpers Qyro", self,
                       objectName="cardTitle")
        self.app_label = QLabel("Aplicación: preparando…", self,
                                objectName="muted")
        self.mode_label = QLabel("Modo: preparando…", self,
                                 objectName="muted")
        self.theme_label = QLabel("Tema: preparando…", self,
                                  objectName="muted")
        for widget in [title, self.app_label, self.mode_label, self.theme_label]:
            layout.addWidget(widget)

    def component_did_mount(self):
        store.dispatch(refresh_runtime_info())

    def update_runtime(self, runtime):
        if hasattr(self, "app_label"):
            mode = "frozen" if runtime["is_frozen"] else "source"
            self.app_label.setText(f"Aplicación: {runtime['app_name']}")
            self.mode_label.setText(f"Modo detectado por is_frozen(): {mode}")
            self.theme_label.setText(f"Tema desde settings: {runtime['theme']}")
