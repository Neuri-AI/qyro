from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from qyro import Component


class UserCard(QFrame, Component):
    """A reusable Qt widget whose keyword arguments become Qyro props."""

    STYLES = (
        "QFrame#card { border-radius: 12px; }"
    )

    def component_will_mount(self):
        self.name = self.props.get("name", "Invitado")
        self.role = self.props.get("role", "Sin rol")

    def render(self):
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        self.name_label = QLabel(self.name, self, objectName="cardTitle")
        self.role_label = QLabel(self.role, self, objectName="muted")

        for widget in [self.name_label, self.role_label]:
            layout.addWidget(widget)

    def on_resize(self):
        if hasattr(self, "role_label"):
            self.role_label.setMaximumWidth(self.calc(self.width(), 90))
