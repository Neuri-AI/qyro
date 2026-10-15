"""
Initialize Engine Use Case.
Orchestrates bootstrapping: verifies environment, sets up telemetry, loads settings,
and prepares the GUI application instance.
"""

from typing import Any, List, Optional
from qyro.application.ports.environment import IEnvironmentPort
from qyro.application.ports.settings import ISettingsPort
from qyro.application.ports.telemetry import ITelemetryPort
from qyro.domain.entities import AppMetadata


class InitializeEngineUseCase:
    """Master bootstrapping use case."""

    def __init__(
        self,
        env_port: IEnvironmentPort,
        settings_port: ISettingsPort,
        telemetry_port: Optional[ITelemetryPort] = None,
    ) -> None:
        self._env = env_port
        self._settings = settings_port
        self._telemetry = telemetry_port

    def execute(self, argv: Optional[List[str]] = None) -> Any:
        # Install telemetry/excepthook if provided. Velto owns GUI startup.
        if self._telemetry:
            self._telemetry.install()

        # Load metadata. UI construction belongs to VeltoContext.
        metadata: AppMetadata = self._settings.load_metadata()

        return {
            "metadata": metadata,
            "platform": self._env.get_platform(),
            "execution_mode": self._env.get_execution_mode(),
            "is_frozen": self._env.is_frozen(),
            "argv": argv,
        }
