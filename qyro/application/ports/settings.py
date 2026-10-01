"""
Settings Port Contract.
Loads build settings, application configuration, and platform overrides.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from qyro.domain.entities import AppMetadata


class ISettingsPort(ABC):
    """Abstract port for loading application configuration and metadata."""

    @abstractmethod
    def load_metadata(self) -> AppMetadata:
        """Loads and returns combined application metadata."""
        pass

    @abstractmethod
    def get_raw_settings(self) -> Dict[str, Any]:
        """Returns the dictionary of loaded settings."""
        pass
