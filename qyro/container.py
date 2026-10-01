"""
Qyro Dependency Injection Container & Composition Root.
Wires Ports, Adapters, and Use Cases together following Clean Architecture.
"""

from pathlib import Path
from typing import Optional

# Ports
from qyro.application.ports.environment import IEnvironmentPort
from qyro.application.ports.resources import IResourcePort
from qyro.application.ports.settings import ISettingsPort
from qyro.application.ports.telemetry import ITelemetryPort
from qyro.application.ports.ui_framework import IUIFrameworkPort

# Adapters
from qyro.adapters.environment.system_environment import SystemEnvironmentAdapter
from qyro.adapters.resources.filesystem_resources import FileSystemResourceAdapter
from qyro.adapters.settings.json_settings import JsonSettingsAdapter
from qyro.adapters.telemetry.console_hook import ConsoleExceptionHookAdapter
from qyro.adapters.telemetry.sentry_hook import SentryExceptionHookAdapter
from qyro.adapters.frameworks.factory import FrameworkFactory

# Use Cases
from qyro.application.use_cases.resolve_resource import ResolveResourceUseCase
from qyro.application.use_cases.load_settings import LoadSettingsUseCase
from qyro.application.use_cases.initialize_engine import InitializeEngineUseCase


class EngineContainer:
    """Composition root for Qyro instances."""

    def __init__(
        self,
        framework_name: Optional[str] = None,
        custom_root: Optional[Path] = None,
        custom_resources_dir: Optional[Path] = None,
        custom_settings_dir: Optional[Path] = None,
        enable_sentry: bool = True,
    ) -> None:
        # 1. Initialize Adapters (Infrastructure)
        self.env_adapter: IEnvironmentPort = SystemEnvironmentAdapter(custom_root=custom_root)
        self.settings_adapter: ISettingsPort = JsonSettingsAdapter(
            env_port=self.env_adapter,
            custom_settings_dir=custom_settings_dir,
        )
        self.resource_adapter: IResourcePort = FileSystemResourceAdapter(
            env_port=self.env_adapter,
            custom_resources_dir=custom_resources_dir,
        )
        # Telemetry selection
        raw_settings = self.settings_adapter.get_raw_settings()
        sentry_dsn = raw_settings.get("sentry_dsn", "")
        if enable_sentry and sentry_dsn:
            self.telemetry_adapter: ITelemetryPort = SentryExceptionHookAdapter(
                dsn=sentry_dsn,
                release=raw_settings.get("version", "0.1.0"),
            )
        else:
            self.telemetry_adapter = ConsoleExceptionHookAdapter()

        # Framework Driver:
        # Automatically infer from base.json "binding" or "framework" if not explicitly specified
        effective_framework = (
            framework_name
            or raw_settings.get("binding")
            or raw_settings.get("framework")
        )
        self.framework_adapter: IUIFrameworkPort = FrameworkFactory.create(effective_framework)

        # 2. Initialize Use Cases (Application Core)
        self.resolve_resource_use_case = ResolveResourceUseCase(self.resource_adapter)
        self.load_settings_use_case = LoadSettingsUseCase(self.settings_adapter)
        self.initialize_engine_use_case = InitializeEngineUseCase(
            env_port=self.env_adapter,
            settings_port=self.settings_adapter,
            framework_port=self.framework_adapter,
            telemetry_port=self.telemetry_adapter,
        )
