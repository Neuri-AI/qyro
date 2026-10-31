<p align="center">
  <img src="https://ik.imagekit.io/kummiktgaiq/ppg/Qyro-logo.svg?updatedAt=1755215983279" alt="Qyro Logo" width="50%">
</p>

# Qyro Runtime

> **Runtime engine for Python applications, providing a cross-platform foundation for desktop and mobile environments.**


[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://python.org)
![GitHub Release](https://img.shields.io/github/v/release/runesc/qyro?include_prereleases&display_name=release&color=stable)
![GitHub Issues](https://img.shields.io/github/issues/runesc/qyro?color=%23ab7df8)
![GitHub Issues Closed](https://img.shields.io/github/issues-closed/runesc/qyro?color=green)
![GitHub forks](https://img.shields.io/github/forks/runesc/qyro)
![GitHub stars](https://img.shields.io/github/stars/runesc/qyro)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Sponsor](https://img.shields.io/badge/Sponsor-Buy%20Me%20a%20Coffee-FFDD00?logo=buymeacoffee&logoColor=000000)](https://buymeacoffee.com/neuri)
> [!IMPORTANT]
> **Qyro Engine v0.1.0 is a beta release.** Runtime APIs and integrations may change. Development currently focuses on desktop applications; mobile support is not yet considered stable.

# Overview

Qyro Engine provides the infrastructure to initialize, configure, and run cross-platform Python applications. It centralizes the application lifecycle, resource resolution, and runtime services.

- **Lifecycle:** initialization, mounting, execution, and resource cleanup through `VeltoContext`.
- **Configuration:** merging general, operating-system-specific, and development-only settings.
- **Resource management:** locating files and assets in both development environments and packaged applications.
- **Protected resources:** reading and verifying compatible resource bundles and encrypted secrets.
- **Development:** coordinating code updates and controlled restarts when needed.
- **Application state:** recovering compatible state during development refreshes.
- **Environment information:** platform detection, execution mode, and metadata.
- **Optional telemetry:** Sentry integration.

## Installation

**Requirements:** Python `>=3.10,<3.14.20`, plus the dependencies of the selected UI framework, where applicable. Availability varies by operating system and Python version.

```shell
python -m pip install qyro-engine==0.1.0
```

Or with Poetry:

```shell
poetry add qyro-engine@0.1.0
```

Optional framework dependencies are available through package extras:

```shell
python -m pip install "qyro-engine[pyside6]==0.1.0"
python -m pip install "qyro-engine[pyqt6]==0.1.0"
python -m pip install "qyro-engine[pyside2]==0.1.0"
python -m pip install "qyro-engine[pyqt5]==0.1.0"
python -m pip install "qyro-engine[kivy]==0.1.0"
python -m pip install "qyro-engine[sentry]==0.1.0"
```

**Note:** Extras install optional dependencies for their respective frameworks, not a complete UI stack. Tkinter depends on your Python/Tk installation. Package availability varies by operating system and Python version.

To develop from this repository:

```shell
git clone https://github.com/Neuri-AI/qyro.git
cd qyro
python -m pip install -e ".[sentry]" pytest
python -m pytest -q
```

## Quick Start

Create the following files in a project with compatible UI dependencies installed:

```text
my-app/
├── main.py
└── settings/
    └── base.json
```

**`settings/base.json`**

```json
{
  "app_name": "My Application",
  "framework": "PySide6",
  "window": {
    "width": 900,
    "height": 600
  }
}
```

**`main.py`**

```python
import sys

from qyro import VeltoContext
from psx import psx


class MyApp(VeltoContext):
    def render(self):
        return psx("""
            <div>
                <h1>Hello, world!</h1>
                <p>Running with Qyro Engine.</p>
            </div>
        """)


if __name__ == "__main__":
    sys.exit(MyApp().run())
```

Run the application using your project's supported development command (or `python main.py` if the dependencies and application environment are installed directly).

Qyro uses the `framework` setting to initialize the renderer and start the application's event loop. The `framework` option must be configured explicitly. If the window dimensions are missing or invalid, Qyro defaults to `800 × 600`.

> [!TIP]
> For project generation and build tools, see [Velto CLI](https://github.com/Neuri-AI/velto-cli).

## UI Frameworks

The `framework` setting supports the following options when starting an application:

| Value | Technology | Considerations |
| --- | --- | --- |
| `PySide6` | Qt 6 | Requires the corresponding dependencies |
| `PyQt6` | Qt 6 | Requires the corresponding dependencies |
| `PySide2` | Qt 5 | Limited wheel availability depending on Python version and platform |
| `PyQt5` | Qt 5 | Requires the corresponding dependencies |
| `Kivy` | Kivy | Compatibility depends on the platform and installed adapter |
| `Tkinter` | Tk | Requires working Tk support in Python |

Compatibility should be verified for each combination of operating system, Python version, and dependencies.

## Configuration

Qyro locates application settings in the project's standard paths and merges them into `app_settings`.

```text
my-app/
├── main.py
├── settings/
│   ├── base.json              # Shared settings
│   ├── windows.json           # Windows-specific settings
│   ├── mac.json               # macOS-specific settings
│   ├── linux.json             # Linux-specific settings
│   ├── development.json       # Development-only settings
│   ├── secrets.json           # Local secrets (do not commit to Git)
│   └── sign.json              # CLI-only; not runtime settings
└── resources/
    ├── base/
    ├── windows/
    ├── mac/
    └── linux/
```

Settings are merged in the following order:

1. `base.json` establishes the default values.
2. The corresponding platform profile overrides those values.
3. `development.json` contains development-specific settings and is applied when running in the development environment. Packaged applications do not load this profile.
4. If a local `secrets.json` file exists, its contents are merged into the settings.
5. The protected resource runtime applies the encrypted secrets payload, if available.

Standard settings profiles are merged recursively for nested objects. The final decrypted secrets payload is applied as top-level keys. The result is available through `app_settings`.

```python
# Inside a VeltoContext subclass:
settings = self.app_settings
app_name = settings.get("app_name", "My Application")
```

### Development Refresh Configuration

Qyro supports optional coordination with the hot reload module. When enabled in the project configuration, compatible store state can be captured and restored during a refresh:

```json
{
  "hot_reload": {
    "preserve_state": true
  }
}
```

Development change notifications use an authenticated local endpoint provided by the supervisor. Incompatible changes—such as modifications to a loaded native extension or a transition of the application's root host—may require a full process restart. The runtime does not enable live updates for packaged applications.

## Stylesheets and Resources

Qyro resolves resource paths whether the application runs from source code or a protected package.

```python
from qyro import get_resource

icon_path = get_resource("icons/app.png")
```

`get_resource()` returns an absolute filesystem path. It accepts multiple path segments and the `required=False` argument when a missing resource should not raise an error.

The application's main context also supports configuring stylesheets for Velto/PSX:

```json
{
  "css": {
    "stylesheets": ["css/styles.css"]
  }
}
```

Alternatively, `VeltoContext` subclasses can define a `stylesheets` tuple containing resource paths. Qyro prepares these resources for use during application rendering.

## Protected Resources and Secrets

Qyro supports compatible protected resource bundles. Protected runtime files are stored under **`.velto/`**:

```text
my-app/
└── .velto/
    ├── resources.pak
    └── runtime*.so / runtime*.pyd
```

Qyro Engine supports encrypting application secrets with AES-256-GCM, using HKDF-SHA256 for key derivation.

At runtime, Qyro locates the protected bundle, verifies its integrity, extracts the relevant `settings/` and `resources/` entries to a temporary runtime location, and makes resources accessible through the standard API. The runtime extension provides the protected cryptographic key material.

> [!WARNING]
> Protected resources and locally encrypted secrets reduce accidental exposure of stored data, but **do not guarantee confidentiality** against someone who controls the distributed application or its runtime memory. Do not include privileged server-side credentials in a client application.

## Runtime API

The public `qyro` module currently exports:

| Symbol | Description |
| --- | --- |
| `VeltoContext` | Base class for the application context |
| `EngineContainer` | Runtime dependency container |
| `PlatformDetector`, `PlatformType` | Platform detection and identifiers |
| `ExecutionMode` | Source or packaged application execution mode |
| `AppMetadata` | Application metadata and original settings |
| `get_resource(*segments, required=True)` | Resolves an application resource to an absolute path |
| `load_build_settings()` | Loads runtime settings into a dictionary |
| `is_frozen()` | Checks whether the application is packaged |
| `QyroEngineError` | Base engine exception |
| `ResourceNotFoundError` | Resource lookup error |
| `SettingsNotFoundError` | Settings lookup error |
| `FrameworkNotAvailableError` | Invalid or unavailable renderer |

### `VeltoContext`

```python
VeltoContext(
    *,
    custom_root: Path | None = None,
    enable_sentry: bool = True,
    argv: list[str] | None = None,
)
```

| Property | Purpose |
| --- | --- |
| `app_settings` | Merged runtime settings |
| `metadata` | Application metadata |
| `platform` | Current operating system enum |
| `execution_mode` | Source or packaged execution mode |
| `is_frozen` | Whether the application is running as a packaged application |
| `container` | Engine dependency container |
| `app` | Mounted application, or `None` before mounting |
| `renderer` | Active renderer, or `None` before mounting |
| `handle` | Native root handle, or `None` before mounting |

A subclass implements `render()` and calls `run()` to start the configured runtime. `VeltoContext` also supports `unmount()` for runtime cleanup. The `app` property represents the mounted application and is not necessarily a native instance of the UI framework.

### Package Names

| Purpose | Name |
| --- | --- |
| Distribution | `qyro-engine` |
| Import | `qyro` |
| Application context | `from qyro import VeltoContext` |

## Compatibility

Qyro Engine is designed for cross-platform application development on **Windows, macOS, Linux, Android, and iOS**.

Compatibility depends on the Python version, operating system, selected UI framework, and its dependencies.

## Qyro Settings Builder

[Velto Settings Builder](https://velto-settings-builder.up.railway.app/) is an auxiliary visual tool for preparing application and release configuration.

## 🤝 Contributing

Contributions to `qyro` are welcome.

1. Fork the repository on GitHub.
2. Create your feature branch (`git checkout -b feature/amazing-feature`).
3. Run test suites (`poetry run pytest`).
4. Commit your changes (`git commit -m 'feat: add amazing feature'`).
5. Push to your branch (`git push origin feature/amazing-feature`).
6. Open a Pull Request.

---

## 📄 License

Distributed under the [MIT License](LICENSE).

Maintained by [Neuri-AI](https://github.com/Neuri-AI). Project maintainer: [@runesc](https://github.com/runesc).
