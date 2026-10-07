from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout
from qyro import Component

from store import profile_slice, store
from .user_card import UserCard


class ProfileEditor(QFrame, Component):
    """Dispatches a profile payload without knowing who consumes it."""

    STYLES = UserCard.STYLES

    def component_will_mount(self):
        self.title = self.props.get("title", "Editor de perfil")

    def render(self):
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        title = QLabel(self.title, self, objectName="cardTitle")
        self.name_input = QLineEdit(
            "Grace Hopper", self, objectName="field", placeholderText="Nombre")
        self.role_input = QLineEdit(
            "Pionera de compiladores", self, objectName="field", placeholderText="Rol")
        send = QPushButton("Enviar payload", self,
                           objectName="primaryButton", clicked=self.send_profile)

        for widget in [title, self.name_input, self.role_input, send]:
            layout.addWidget(widget)

    def send_profile(self):
        payload = {
            "name": self.name_input.text().strip() or "Sin nombre",
            "role": self.role_input.text().strip() or "Sin rol",
        }
        store.dispatch(profile_slice.actions.set_profile(payload))
