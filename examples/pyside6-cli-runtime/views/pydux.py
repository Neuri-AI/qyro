"""Qyro Component page widgets composed into the main tab layout."""

from PySide6.QtWidgets import QLabel
from views.root import Root
from components import CounterCard
from store import store

class PyduxView(Root):
    def component_did_mount(self):
        self.counter_card = CounterCard(parent=self, title="CounterCard conectado a Pydux")
        inspector = getattr(store, "inspector", None)
        if inspector:
            message = QLabel(
                f'<a href="{inspector.base_url}">Abre Pydux DevTools en {inspector.base_url}</a> para ver cada dispatch y usar time travel.',
                self,
                objectName="devtoolsLink",
                openExternalLinks=True,
                wordWrap=True,
            )
        else:
            message = QLabel(
                "Pydux DevTools está desactivado en la versión frozen.",
                self,
                objectName="muted",
                wordWrap=True,
            )
        
        for widget in [self.counter_card, message]:
            self.layout.addWidget(widget)

    def cleanup(self):
        self.counter_card.component_will_unmount()
