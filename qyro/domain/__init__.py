"""
Qyro - Domain Layer
Pure business logic, entities, value objects, and domain errors.
Free from any external GUI, CLI, or filesystem framework dependencies.
"""

from .entities import (
    PlatformType,
    ExecutionMode,
    AppMetadata,
    ResourceQuery,
    ResourceResult,
)
from .errors import (
    QyroEngineError,
    ResourceNotFoundError,
    SettingsNotFoundError,
    FrameworkNotAvailableError,
    PlatformUnsupportedError,
)

__all__ = [
    "PlatformType",
    "ExecutionMode",
    "AppMetadata",
    "ResourceQuery",
    "ResourceResult",
    "QyroEngineError",
    "ResourceNotFoundError",
    "SettingsNotFoundError",
    "FrameworkNotAvailableError",
    "PlatformUnsupportedError"
]
