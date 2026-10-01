"""
Qyro.
Clean Architecture runtime engine and lifecycle framework for Python desktop GUI apps.
Decoupled from CLI tools, independent and multi-toolkit ready.
"""

from qyro.client.context import ApplicationContext
from qyro.client.component import Component, PPGLifeCycle
from qyro.container import EngineContainer
from qyro.adapters.platform.detector import PlatformDetector
from qyro.domain.entities import PlatformType, ExecutionMode, AppMetadata
from qyro.domain.errors import (
    QyroEngineError,
    ResourceNotFoundError,
    SettingsNotFoundError,
    FrameworkNotAvailableError,
)

__version__ = "0.1.0"

# Module-level singleton container for quick procedural usage
_default_container: EngineContainer | None = None


def _get_default_container() -> EngineContainer:
    global _default_container
    app_container = ApplicationContext._global_container
    if app_container is not None:
        _default_container = app_container
        return app_container

    if _default_container is None:
        _default_container = EngineContainer()
    return _default_container


def get_resource(*segments: str, required: bool = True) -> str:
    """Convenience helper to resolve resource path without manually creating ApplicationContext."""
    container = _get_default_container()
    return str(container.resolve_resource_use_case.execute(*segments, required=required))


def load_build_settings() -> dict:
    """Convenience helper to load build settings dictionary."""
    container = _get_default_container()
    return container.load_settings_use_case.execute().raw_settings


def is_frozen() -> bool:
    """Convenience helper to check if running in a frozen executable."""
    container = _get_default_container()
    return container.env_adapter.is_frozen()


# Backward compatibility alias
app_is_frozen = is_frozen


__all__ = [
    "ApplicationContext",
    "Component",
    "PPGLifeCycle",
    "EngineContainer",
    "PlatformDetector",
    "PlatformType",
    "ExecutionMode",
    "AppMetadata",
    "QyroEngineError",
    "ResourceNotFoundError",
    "SettingsNotFoundError",
    "FrameworkNotAvailableError",
    "get_resource",
    "load_build_settings",
    "is_frozen",
    "app_is_frozen",
]
