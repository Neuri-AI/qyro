"""Qyro Component page widgets composed into the main tab layout."""

from PySide6.QtWidgets import QLabel
from views.root import Root
from components import RuntimeInfoCard

class ContextView(Root):
    def component_did_mount(self):
        settings = self.app_settings
        for row in (
            f"Identifier: {self.context.metadata.identifier if self.context else settings.get('identifier', 'sin identifier')}",
            f"Execution mode: {self.context.execution_mode.value if self.context else 'no inyectado'}",
            f"Theme custom: {settings.get('theme')}",
            f"Window settings: {settings.get('window')}",
            f"Frozen por helper: {self.is_frozen}",
        ):
            self.layout.addWidget(QLabel(row, self))
        self.runtime_card = RuntimeInfoCard(parent=self)
        self.layout.addWidget(self.runtime_card)

    def cleanup(self):
        self.runtime_card.component_will_unmount()
