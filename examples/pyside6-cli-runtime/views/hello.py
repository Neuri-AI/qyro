"""Qyro Component page widgets composed into the main tab layout."""

from views.root import Root
from PySide6.QtWidgets import QLabel
from qyro import PlatformDetector

class HelloView(Root):
    def component_did_mount(self):
        settings = self.app_settings
        self.layout.addWidget(QLabel(
            f"App: {settings.get('app_name')} v{settings.get('version')}", self
        ))
        self.layout.addWidget(QLabel(
            f"Platform: {self.context.platform.value if self.context else PlatformDetector.get_platform().value} | frozen: {self.is_frozen}", self
        ))
