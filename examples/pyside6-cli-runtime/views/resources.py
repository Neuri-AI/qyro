"""Qyro Component page widgets composed into the main tab layout."""
from pathlib import Path
from PySide6.QtWidgets import QLabel, QPushButton
from views.root import Root

class ResourcesView(Root):
    def component_did_mount(self):
        greeting = Path(self.get_resource("text/greeting.txt")
                        ).read_text(encoding="utf-8")
        optional = Path(self.get_resource(
            "themes/seasonal.qss", required=False))
        listed = sorted(
            path.name
            for path in self.context.container.resource_adapter.list_resources(
                "base",
            )
        )

        button = QPushButton("Aplicar QSS desde resources", self, objectName="primaryButton",
                             clicked=lambda: (
                                 self.context.set_styles(self.get_resource("styles/demo.qss"))
                                 if self.context else
                                 self.set_styles(self.get_resource("styles/demo.qss"))
                             ))

        for widget in [
            QLabel(greeting, self),
            QLabel(f"Recurso opcional existe: {optional.is_file()}", self),
            QLabel(f"Contenido de resources/text: {', '.join(listed)}", self),
            button
        ]:
            self.layout.addWidget(widget)
