"""Qyro Component page widgets composed into the main tab layout."""


from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from qyro.client.component import Component

class Root(QWidget, Component):
    """Common page shell with explicit context and Component helpers."""

    def component_will_mount(self):
        self.context = self.props.get("context")
        self.title = self.props["title"]
        self.detail = self.props["detail"]

    def render(self):
        self.setObjectName("pageRoot")
        self.layout = QVBoxLayout(self)
        eyebrow = QLabel(self.__class__.__name__.replace(
            "View", "").upper(), self, objectName="eyebrow")
        heading = QLabel(self.title, self, objectName="pageTitle")
        detail = QLabel(self.detail, self,
                        objectName="pageDescription", wordWrap=True)

        for widget in [eyebrow, heading, detail]:
            self.layout.addWidget(widget)
