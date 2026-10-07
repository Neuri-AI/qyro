from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from pydux.adapters.qyro import Reactive
from qyro import Component

from store import counter_slice, select_counter_label, store
from .user_card import UserCard


class CounterCard(QFrame, Component, Reactive):
    """A prop-driven component that owns its Pydux subscription and actions."""

    STYLES = UserCard.STYLES

    def component_will_mount(self):
        self.title = self.props.get("title", "Contador")
        self.bind_selector(store, select_counter_label,
                           self.update_counter_label)

    def render(self):
        self.setObjectName("card")
        layout = QVBoxLayout(self)

        title = QLabel(self.title, self, objectName="cardTitle")
        self.counter_label = QLabel(
            "Preparando store…", self, objectName="muted")

        plus = QPushButton("+1", self, objectName="primaryButton",
                           clicked=lambda: store.dispatch(counter_slice.actions.increment()))
        minus = QPushButton("−1", self, objectName="primaryButton",
                            clicked=lambda: store.dispatch(counter_slice.actions.decrement()))

        for widget in [title, self.counter_label, plus, minus]:
            layout.addWidget(widget)

    def update_counter_label(self, text):
        if hasattr(self, "counter_label"):
            self.counter_label.setText(text)
