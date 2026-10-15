"""Qyro Component page widgets composed into the main tab layout."""

from pathlib import Path
from PySide6.QtWidgets import QLabel
from views.root import Root
from qyro import EngineContainer

class ContainerView(Root):
    def component_did_mount(self):
        isolated = EngineContainer(
            framework_name="Headless", custom_root=Path(__file__).parents[1], enable_sentry=False
        )
        metadata = isolated.load_settings_use_case.execute()
        for row in (
            f"Adaptador UI de ApplicationContext: {type(self.context.container.framework_adapter).__name__ if self.context else 'no inyectado'}",
            f"Adaptador UI Headless: {type(isolated.framework_adapter).__name__}",
            f"Adaptador resources: {type(isolated.resource_adapter).__name__}",
            f"Adaptador telemetry: {type(isolated.telemetry_adapter).__name__}",
            f"Headless metadata: {metadata.app_name} ({metadata.version})",
            f"Use case resource: {isolated.resolve_resource_use_case.execute('text/greeting.txt')}",
        ):
            self.layout.addWidget(QLabel(row, self))
