"""
Load Settings Use Case.
Encapsulates loading and validating application metadata and build configuration.
"""

from typing import Any
from qyro.application.ports.settings import ISettingsPort
from qyro.domain.entities import AppMetadata


class LoadSettingsUseCase:
    """Use case to load configuration and return validated AppMetadata."""

    def __init__(self, settings_port: ISettingsPort) -> None:
        self._settings_port = settings_port
        self._cached_metadata: AppMetadata | None = None

    def execute(self, force_reload: bool = False) -> AppMetadata:
        if self._cached_metadata is None or force_reload:
            self._cached_metadata = self._settings_port.load_metadata()
        return self._cached_metadata

    def get_setting(self, key: str, default: Any = None) -> Any:
        metadata = self.execute()
        return metadata.get(key, default)
