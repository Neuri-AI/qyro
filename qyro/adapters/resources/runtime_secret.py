from __future__ import annotations

import importlib.util
from importlib.machinery import ExtensionFileLoader
from pathlib import Path


_RUNTIME_SECRET_MODULE_STEM = "runtime"


def find_runtime_secret_module(qyro_dir: Path) -> Path | None:
    candidates = [
        *sorted(qyro_dir.glob(f"{_RUNTIME_SECRET_MODULE_STEM}*.so")),
        *sorted(qyro_dir.glob(f"{_RUNTIME_SECRET_MODULE_STEM}*.pyd")),
        *sorted(qyro_dir.glob(f"{_RUNTIME_SECRET_MODULE_STEM}*.dylib")),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def read_runtime_secret(secret_module_path: Path) -> bytes:
    loader = ExtensionFileLoader(_RUNTIME_SECRET_MODULE_STEM, str(secret_module_path))
    spec = importlib.util.spec_from_file_location(
        _RUNTIME_SECRET_MODULE_STEM,
        str(secret_module_path),
        loader=loader,
    )
    if spec is None:
        raise ValueError("Unable to load runtime secret module spec")

    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)

    value = getattr(module, "RUNTIME_SECRET_HEX", None)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Runtime secret not found in runtime module")

    try:
        secret = bytes.fromhex(value.strip())
    except ValueError as exc:
        raise ValueError("Invalid runtime secret hex format") from exc

    if len(secret) < 16:
        raise ValueError("Runtime secret is too short")

    return secret
