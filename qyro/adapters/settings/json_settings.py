"""
JSON Settings Adapter.
Implements ISettingsPort by loading base.json and platform-specific JSON settings.
"""

import json
from pathlib import Path
from typing import Any, Dict
from qyro.application.ports.environment import IEnvironmentPort
from qyro.adapters.resources.runtime_secret import (
    find_runtime_secret_module,
    read_runtime_secret,
)
from qyro.adapters.resources.secrets_crypto import decrypt_secrets_payload
from qyro.application.ports.settings import ISettingsPort
from qyro.adapters.resources.protected_bundle import ProtectedResourceBundle
from qyro.domain.entities import AppMetadata, PlatformType


class JsonSettingsAdapter(ISettingsPort):
    """Loads and merges hierarchical JSON configuration files."""

    _SECRETS_FILE_NAME = "secrets.json"
    _LEGACY_ENCRYPTED_SECRETS_FILE_NAME = "secrets.json"

    def __init__(self, env_port: IEnvironmentPort, custom_settings_dir: Path | None = None) -> None:
        self._env = env_port
        self._custom_settings_dir = custom_settings_dir
        self._cached_settings: Dict[str, Any] | None = None

    def _find_settings_dir(self) -> Path | None:
        if self._custom_settings_dir and self._custom_settings_dir.exists():
            return self._custom_settings_dir

        root = self._env.get_bundle_dir() if self._env.is_frozen() else self._env.get_root_dir()

        # In development / source mode, prioritize local workspace settings
        if not self._env.is_frozen():
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

        # When running frozen, or when local settings are absent, load protected package
        protected_root = ProtectedResourceBundle.get_extracted_root(self._env)
        if protected_root:
            protected_settings = protected_root / "settings"
            if protected_settings.exists() and (protected_settings / "base.json").exists():
                return protected_settings

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

            self._apply_plain_secrets_override(settings_dir, combined)

        self._apply_encrypted_secrets_override(combined)

        self._cached_settings = combined
        return combined

    def _apply_plain_secrets_override(self, settings_dir: Path, combined: Dict[str, Any]) -> None:
        secrets_file = settings_dir / self._SECRETS_FILE_NAME
        if not secrets_file.exists():
            root = self._env.get_bundle_dir() if self._env.is_frozen() else self._env.get_root_dir()
            fallback = root / "settings" / self._SECRETS_FILE_NAME
            if fallback.exists():
                secrets_file = fallback
            else:
                return
        try:
            with open(secrets_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                combined.update(data)
        except Exception:
            pass

    def _apply_encrypted_secrets_override(self, combined: Dict[str, Any]) -> None:
        embedded_payload = ProtectedResourceBundle.get_encrypted_secrets_payload(self._env)
        if embedded_payload is not None:
            runtime_module_path = self._find_runtime_module_for_encrypted_secrets()
            if runtime_module_path is None:
                raise ValueError("Encrypted secrets were found but the runtime secret module is missing")
            runtime_secret = read_runtime_secret(runtime_module_path)
            plaintext = decrypt_secrets_payload(embedded_payload, runtime_secret)
            self._merge_decrypted_secrets_payload(plaintext, combined)
            return

        # Backward compatibility with older bundles that shipped .qyro/secrets.json
        encrypted_path = self._legacy_encrypted_secrets_path()
        if not encrypted_path.exists():
            return

        runtime_module_path = find_runtime_secret_module(encrypted_path.parent)
        if runtime_module_path is None:
            raise ValueError("Encrypted secrets were found but the runtime secret module is missing")

        runtime_secret = read_runtime_secret(runtime_module_path)
        plaintext = decrypt_secrets_payload(encrypted_path.read_bytes(), runtime_secret)

        self._merge_decrypted_secrets_payload(plaintext, combined)

    def _merge_decrypted_secrets_payload(self, plaintext: bytes, combined: Dict[str, Any]) -> None:
        try:
            data = json.loads(plaintext.decode("utf-8"))
        except Exception as exc:
            raise ValueError("Encrypted secrets payload is not valid UTF-8 JSON") from exc

        if not isinstance(data, dict):
            raise ValueError("Encrypted secrets JSON must contain an object")

        combined.update(data)

    def _find_runtime_module_for_encrypted_secrets(self) -> Path | None:
        root = self._env.get_bundle_dir() if self._env.is_frozen() else self._env.get_root_dir()
        return find_runtime_secret_module(root / ".qyro")

    def _legacy_encrypted_secrets_path(self) -> Path:
        root = self._env.get_bundle_dir() if self._env.is_frozen() else self._env.get_root_dir()
        return root / ".qyro" / self._LEGACY_ENCRYPTED_SECRETS_FILE_NAME

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
