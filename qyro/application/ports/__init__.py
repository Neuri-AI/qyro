"""
Qyro - Application Layer Ports (Interfaces).
Contracts that define how use cases interact with infrastructure/adapters.
"""

from .environment import IEnvironmentPort
from .resources import IResourcePort
from .settings import ISettingsPort
from .ui_framework import IUIFrameworkPort
from .telemetry import ITelemetryPort

__all__ = [
    "IEnvironmentPort",
    "IResourcePort",
    "ISettingsPort",
    "IUIFrameworkPort",
    "ITelemetryPort",
]
