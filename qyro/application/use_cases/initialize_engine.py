"""
Initialize Engine Use Case.
Orchestrates bootstrapping: verifies environment, sets up telemetry, loads settings,
and prepares the GUI application instance.
"""

from typing import Any, List, Optional
from qyro.application.ports.environment import IEnvironmentPort
from qyro.application.ports.settings import ISettingsPort
from qyro.application.ports.telemetry import ITelemetryPort
from qyro.application.ports.ui_framework import IUIFrameworkPort
from qyro.domain.entities import AppMetadata
from qyro.domain.errors import FrameworkNotAvailableError


class InitializeEngineUseCase:
    """Master bootstrapping use case."""

    def __init__(
        self,
        env_port: IEnvironmentPort,
        settings_port: ISettingsPort,
        framework_port: IUIFrameworkPort,
        telemetry_port: Optional[ITelemetryPort] = None,
    ) -> None:
        self._env = env_port
        self._settings = settings_port
        self._framework = framework_port
        self._telemetry = telemetry_port

    def execute(self, argv: Optional[List[str]] = None) -> Any:
        # 1. Validate framework availability
        if not self._framework.is_available():
            raise FrameworkNotAvailableError(self._framework.framework_name)

        # 2. Install telemetry/excepthook if provided
        if self._telemetry:
            self._telemetry.install()

        # 3. Load metadata
        metadata: AppMetadata = self._settings.load_metadata()

        # 4. Instantiate the native framework application
        app_instance = self._framework.create_application(argv)

        return {
            "app_instance": app_instance,
            "metadata": metadata,
            "platform": self._env.get_platform(),
            "execution_mode": self._env.get_execution_mode(),
            "is_frozen": self._env.is_frozen(),
        }
