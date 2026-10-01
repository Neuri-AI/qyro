"""
Qyro - Adapters Layer.
Concrete implementations of application ports.
"""

from .environment.system_environment import SystemEnvironmentAdapter
from .settings.json_settings import JsonSettingsAdapter
from .resources.filesystem_resources import FileSystemResourceAdapter
from .telemetry.console_hook import ConsoleExceptionHookAdapter
from .telemetry.sentry_hook import SentryExceptionHookAdapter
from .platform.detector import PlatformDetector
from .frameworks.factory import FrameworkFactory

__all__ = [
    "SystemEnvironmentAdapter",
    "JsonSettingsAdapter",
    "FileSystemResourceAdapter",
    "ConsoleExceptionHookAdapter",
    "SentryExceptionHookAdapter",
    "PlatformDetector",
    "FrameworkFactory",
]
