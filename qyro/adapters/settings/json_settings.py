"""
JSON Settings Adapter.
Implements ISettingsPort by loading base.json and platform-specific JSON settings.
"""

import json
from pathlib import Path
from typing import Any, Dict
from qyro.application.ports.environment import IEnvironmentPort
from qyro.application.ports.settings import ISettingsPort
from qyro.adapters.resources.protected_bundle import ProtectedResourceBundle
from qyro.domain.entities import AppMetadata, PlatformType


class JsonSettingsAdapter(ISettingsPort):
    """Loads and merges hierarchical JSON configuration files."""

    def __init__(self, env_port: IEnvironmentPort, custom_settings_dir: Path | None = None) -> None:
        self._env = env_port
        self._custom_settings_dir = custom_settings_dir
        self._cached_settings: Dict[str, Any] | None = None

    def _find_settings_dir(self) -> Path | None:
        if self._custom_settings_dir and self._custom_settings_dir.exists():
            return self._custom_settings_dir

        protected_root = ProtectedResourceBundle.get_extracted_root(self._env)
        if protected_root:
            protected_settings = protected_root / "settings"
            if protected_settings.exists() and (protected_settings / "base.json").exists():
                return protected_settings

        root = self._env.get_bundle_dir() if self._env.is_frozen() else self._env.get_root_dir()

        possible_dirs = [
            root / "settings",
            root / "build" / "settings",
            root / "src" / "main" / "settings",
            root / "src" / "build" / "settings",
            root,
        ]
        for d in possible_dirs:
            if d.exists() and (d / "base.json").exists():
                return d
        return None

    def get_raw_settings(self) -> Dict[str, Any]:
        if self._cached_settings is not None:
            return self._cached_settings

        combined: Dict[str, Any] = {}
        settings_dir = self._find_settings_dir()

        if settings_dir:
            # 1. Load base.json
            base_file = settings_dir / "base.json"
            if base_file.exists():
                try:
                    with open(base_file, "r", encoding="utf-8") as f:
                        combined.update(json.load(f))
                except Exception:
                    pass

            # 2. Load platform override
            platform = self._env.get_platform()
            platform_files = {
                PlatformType.WINDOWS: ["windows.json", "win32.json"],
                PlatformType.MACOS: ["mac.json", "darwin.json"],
                PlatformType.LINUX: ["linux.json"],
            }
            for filename in platform_files.get(platform, []):
                p_file = settings_dir / filename
                if p_file.exists():
                    try:
                        with open(p_file, "r", encoding="utf-8") as f:
                            combined.update(json.load(f))
                        break
                    except Exception:
                        pass

        self._cached_settings = combined
        return combined

    def load_metadata(self) -> AppMetadata:
        raw = self.get_raw_settings()
        return AppMetadata(
            app_name=raw.get("app_name", "QyroApp"),
            version=raw.get("version", "1.0.0"),
            author=raw.get("author", "Developer"),
            identifier=raw.get("identifier", "com.qyro.app"),
            description=raw.get("description", ""),
            raw_settings=raw,
        )
