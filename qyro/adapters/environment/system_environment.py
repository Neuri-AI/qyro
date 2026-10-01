"""
System Environment Adapter.
Implements IEnvironmentPort for PyInstaller, cx_Freeze, and Source environments.
"""

import sys
from pathlib import Path
from qyro.application.ports.environment import IEnvironmentPort
from qyro.domain.entities import ExecutionMode, PlatformType
from qyro.adapters.platform.detector import PlatformDetector


class SystemEnvironmentAdapter(IEnvironmentPort):
    """Detects runtime execution specifics across operating systems."""

    def __init__(self, custom_root: Path | None = None) -> None:
        self._custom_root = custom_root

    def is_frozen(self) -> bool:
        return getattr(sys, "frozen", False)

    def get_execution_mode(self) -> ExecutionMode:
        if self.is_frozen():
            if hasattr(sys, "_MEIPASS"):
                return ExecutionMode.FROZEN_PYINSTALLER
            return ExecutionMode.FROZEN_GENERIC
        return ExecutionMode.SOURCE

    def get_platform(self) -> PlatformType:
        return PlatformDetector.get_platform()

    def get_root_dir(self) -> Path:
        if self._custom_root:
            return self._custom_root

        if self.is_frozen():
            # Executable directory
            return Path(sys.executable).resolve().parent

        # Source mode: find project root containing pyproject.toml or src/
        cwd = Path.cwd()
        for parent in [cwd] + list(cwd.parents):
            if (parent / "pyproject.toml").exists() or (parent / "src").exists():
                return parent
        return cwd

    def get_bundle_dir(self) -> Path:
        if self.is_frozen() and hasattr(sys, "_MEIPASS"):
            return Path(getattr(sys, "_MEIPASS")).resolve()

        # macOS bundle check
        if self.is_frozen() and sys.platform == "darwin":
            mac_resources = Path(sys.executable).resolve().parent.parent / "Resources"
            if mac_resources.exists():
                return mac_resources

        return self.get_root_dir()
