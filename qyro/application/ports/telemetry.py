"""
Telemetry and Exception Hook Port Contract.
Standardized interception of unhandled errors for user alerts and monitoring.
"""

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional, Type


class ITelemetryPort(ABC):
    """Abstract port for error reporting and global exception hooks."""

    @abstractmethod
    def install(self) -> None:
        """Installs the global exception hook (e.g. into sys.excepthook)."""
        pass

    @abstractmethod
    def handle_exception(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback: Optional[TracebackType],
    ) -> None:
        """Handles an intercepted uncaught exception."""
        pass
