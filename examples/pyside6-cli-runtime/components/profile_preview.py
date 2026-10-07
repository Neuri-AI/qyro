from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from pydux.adapters.qyro import Reactive
from qyro import Component
from store import select_profile, store
from .user_card import UserCard


class ProfilePreview(QFrame, Component, Reactive):
    """Consumes the profile selector and renders a payload sent by another component."""

    STYLES = UserCard.STYLES

    def component_will_mount(self):
        self.title = self.props.get("title", "Vista previa")
        self.bind_selector(store, select_profile, self.update_profile)

    def render(self):
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        title = QLabel(self.title, self, objectName="cardTitle")
        self.name_label = QLabel(
            "Nombre: preparando…", self, objectName="muted")
        self.role_label = QLabel("Rol: preparando…", self, objectName="muted")

        for widget in [title, self.name_label, self.role_label]:
            layout.addWidget(widget)

    def update_profile(self, profile):
        if hasattr(self, "name_label"):
            self.name_label.setText(f"Nombre: {profile['name']}")
            self.role_label.setText(f"Rol: {profile['role']}")