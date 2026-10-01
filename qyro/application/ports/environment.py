"""
Environment Port Contract.
Detects platform, frozen/development execution, and root paths.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from qyro.domain.entities import ExecutionMode, PlatformType


class IEnvironmentPort(ABC):
    """Abstract port for querying runtime environment details."""

    @abstractmethod
    def is_frozen(self) -> bool:
        """Returns True if running compiled (e.g. PyInstaller), False if source."""
        pass

    @abstractmethod
    def get_execution_mode(self) -> ExecutionMode:
        """Returns specific execution mode enum."""
        pass

    @abstractmethod
    def get_platform(self) -> PlatformType:
        """Returns the detected host OS platform."""
        pass

    @abstractmethod
    def get_root_dir(self) -> Path:
        """Returns root directory of application source code or frozen executable."""
        pass

    @abstractmethod
    def get_bundle_dir(self) -> Path:
        """Returns temporary or bundled resources directory (e.g. _MEIPASS or Contents/Resources)."""
        pass
