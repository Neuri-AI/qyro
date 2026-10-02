<p align="center">
  <img src="https://ik.imagekit.io/kummiktgaiq/ppg/Qyro-logo.svg?updatedAt=1755215983279" alt="Qyro Logo" width="50%">
</p>

> [!WARNING]
> **Qyro is currently in alpha.** APIs, adapters, and behavior may change between releases.
> Desktop workflows are the current focus. Mobile support is not yet considered stable.


# ⚡ Qyro Runtime

> **Runtime engine for Python applications, providing a cross-platform foundation for desktop and mobile environments.**


[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://python.org)
![GitHub Release](https://img.shields.io/github/v/release/runesc/qyro?include_prereleases&display_name=release&color=stable)
![GitHub Issues](https://img.shields.io/github/issues/runesc/qyro?color=%23ab7df8)
![GitHub Issues Closed](https://img.shields.io/github/issues-closed/runesc/qyro?color=green)
![GitHub forks](https://img.shields.io/github/forks/runesc/qyro)
![GitHub stars](https://img.shields.io/github/stars/runesc/qyro)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Sponsor](https://img.shields.io/badge/Sponsor-Buy%20Me%20a%20Coffee-FFDD00?logo=buymeacoffee&logoColor=000000)](https://buymeacoffee.com/neuri)


> [!NOTE]
> **Need the Qyro automation and build tools?** This repository contains the **Qyro Runtime**, which provides the application context, framework adapters, resource handling, and component lifecycle for Python GUI applications. For **project scaffolding, build automation, packaging, distribution, code signing, and release workflows**, see **[Qyro CLI](https://github.com/Neuri-AI/qyro-cli)**.


## What it is

Qyro currently provides:

- A runtime container that wires settings, resource lookup, telemetry hook, and UI adapter.
- A single ApplicationContext API for Qt, Tkinter, and Kivy style apps.
- Automatic settings loading from JSON files.
- Resource resolution that works in source mode and frozen mode.
- A component lifecycle mixin for UI classes with flexible property handling.

## What it is not

Qyro is not the build/distribution CLI.

- Build, bundle, signing, notarization: qyro-cli concern.
- Web bridge APIs from legacy PPG examples: not part of qyro public API.

## Supported UI adapters

Framework adapters available in the engine:

- PySide6
- PyQt6
- PySide2
- PyQt5
- Kivy
- Tkinter
- Headless fallback

Adapter selection behavior:

- If binding/framework is provided in settings, it is used.
- Otherwise the engine auto-detects in this order:
  PySide6 -> PyQt6 -> PySide2 -> PyQt5 -> Kivy -> Tkinter -> Headless

## Compatibility

A check mark indicates that the complete workflow has been validated for
the specified framework, platform, and Python version.

`init → start → build → bundle`

| Framework | Platform | Python 3.10 | Python 3.11 | Python 3.12 | Python 3.13 | Python 3.14 |
|---|---|---:|---:|---:|---:|---:|
| PySide6 | Windows | — | — | — | — | — |
| PySide6 | macOS | — | — | — | — | — |
| PySide6 | Linux | — | — | — | — | — |
| PyQt6 | Windows | — | — | — | — | — |
| PyQt6 | macOS | — | — | — | — | — |
| PyQt6 | Linux | — | — | — | — | — |
| PyQt5 | Windows | — | — | — | — | — |
| PyQt5 | macOS | — | — | — | — | — |
| PyQt5 | Linux | — | — | — | — | — |
| Kivy | Windows | — | — | — | — | — |
| Kivy | macOS | — | — | — | — | — |
| Kivy | Linux | — | — | — | — | — |
| Tkinter | Windows | — | — | — | — | — |
| Tkinter | macOS | — | — | — | — | — |
| Tkinter | Linux | — | — | — | — | — |

> Other combinations may work but have not yet been validated through the
> complete workflow.

## Installation

This package is configured with Poetry extras.

Base package:

```bash
poetry add qyro

```

With specific GUI stack:

```bash
poetry add qyro -E pyside6
poetry add qyro -E pyqt6
poetry add qyro -E pyside2
poetry add qyro -E pyqt5
poetry add qyro -E kivy

```

With telemetry helper:

```bash
poetry add qyro -E sentry

```

Everything enabled:

```bash
poetry add qyro -E all

```

## Expected project layout

Qyro looks for settings and resources in common locations.
Resources are resolved from OS-specific folders first, then base folders.
Typical layout:

```text
my-app/
├─ main.py
├─ settings/
│  ├─ base.json
│  ├─ windows.json
│  ├─ mac.json
│  └─ linux.json
└─ resources/
   ├─ base/
   ├─ windows/
   ├─ mac/
   └─ linux/

```

## Qyro Settings Builder

Configuring application settings and release options manually can be
time-consuming and error-prone. The **Qyro Settings Builder** provides a
visual interface for creating and managing the settings used by Qyro
projects.

It helps configure:

- Application settings.
- Platform-specific settings.
- Resource-related options.
- Release and packaging settings.
- Distribution metadata.

Use the online builder here:

[Open Qyro Settings Builder](https://qyro-settings-builder.up.railway.app/)

The generated configuration files can be placed in the project's `settings/`
directory and reviewed or customized before running Qyro CLI commands.
> [!NOTE]
> The Settings Builder is an auxiliary tool for preparing configuration files.
> The final settings remain part of your project and should be reviewed before
> building or releasing an application.

## Quick start (Qt)

```python
import sys
from PySide6.QtWidgets import QMainWindow, QLabel
from qyro import ApplicationContext
from qyro.ui.component import Component


class MyWindow(QMainWindow, Component, ApplicationContext):
    def component_will_mount(self):
        self.resize(640, 480)

    def render(self):
        label = QLabel(
            f"App: {self.window_title}\n"
            f"Platform: {self.platform.value}\n"
            f"Frozen: {self.is_frozen}",
            parent=self,
        )
        label.move(24, 24)


if __name__ == "__main__":
    window = MyWindow()
    window.show()
    sys.exit(window.run())

```

## Quick start (Kivy)

```python
from kivy.app import App
from kivy.uix.label import Label
from kivy.core.window import Window
from qyro import ApplicationContext
from qyro.ui.component import Component


class MyKvApp(App, Component, ApplicationContext):

    def component_will_mount(self):
        Window.size = (640, 480)

    def render(self):
        label = Label(
            text=(
                f"Hello, World!\n\n"
                f"App Title: {self.window_title}\n"
                f"Platform: {self.platform.value} (Frozen: {self.is_frozen})\n\n"
            ),
            halign="left",
            valign="middle",
        )
        label.bind(size=label.setter("text_size"))
        return label

    def build(self):
        return self.render()

if __name__ == "__main__":
    MyKvApp().run()

```

## Quick start (Tkinter)

```python
import tkinter as tk
from qyro import ApplicationContext
from qyro.ui.component import Component


class MyTkApp(tk.Tk, Component, ApplicationContext):
    def component_will_mount(self):
        self.geometry("480x240")

    def render(self):
        tk.Label(
            self,
            text=f"{self.window_title} | {self.platform.value} | frozen={self.is_frozen}",
        ).pack(padx=16, pady=16)


if __name__ == "__main__":
    app = MyTkApp()
    app.run()

```

## API Reference

This section documents the public runtime API that is available in the current codebase.

### Top-level API (`qyro`)

Exports:

* ApplicationContext
* Component
* EngineContainer
* PlatformDetector
* PlatformType
* ExecutionMode
* AppMetadata
* QyroEngineError
* ResourceNotFoundError
* SettingsNotFoundError
* FrameworkNotAvailableError
* get_resource
* load_build_settings
* is_frozen

Function signatures:

```python
def get_resource(*segments: str, required: bool = True) -> str
def load_build_settings() -> dict
def is_frozen() -> bool

```

Behavior notes:

* get_resource returns an absolute path string.
* If required=True and a resource is not found, the resolver may raise a runtime error.

### ApplicationContext

Constructor:

```python
ApplicationContext(
    framework: str | None = None,
    custom_root: Path | None = None,
    enable_sentry: bool = True,
    argv: list[str] | None = None,
    *args,
    **kwargs,
)

```

Parameter reference:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `framework` | `str \| None` | `None` | Forces a specific framework adapter. |
| `custom_root` | `Path \| None` | `None` | Overrides the project root directory. |
| `enable_sentry` | `bool` | `True` | Enables the Sentry hook when a DSN is available. |
| `argv` | `list[str] \| None` | `None` | Optional arguments passed when creating the application. |

Property reference:

| Property | Type | Description |
|---|---|---|
| `container` | `EngineContainer` | The underlying dependency container instance. |
| `app` | `Any` | The native framework application instance, such as `QApplication`, a Tk root, or a Kivy app. |
| `metadata` | `AppMetadata` | Application metadata loaded from the settings. |
| `app_settings` | `dict[str, Any]` | The final merged settings dictionary. |
| `is_frozen` | `bool` | Indicates whether the application is running from a frozen bundle. |
| `platform` | `PlatformType` | The detected platform enum value. |
| `execution_mode` | `ExecutionMode` | The current execution mode: source or frozen. |
| `window_title` | `str` | The current window title, with getter and setter support. |
| `app_icon` | `str \| None` | The resolved application icon path, with setter support. |

Method reference:

| Method | Signature | Returns | Notes |
|---|---|---|---|
| `get_default_window_title` | `get_default_window_title()` | `str` | Uses the metadata-to-`app_name` fallback chain. |
| `get_window_title` | `get_window_title()` | `str` | Reads the current title from the native window when possible. |
| `set_window_title` | `set_window_title(title, window=None)` | `bool` | Best-effort cross-toolkit title assignment. |
| `get_app_icon_path` | `get_app_icon_path()` | `str \| None` | Automatically discovers the icon from settings and resource conventions. |
| `set_window_icon` | `set_window_icon(icon_path_or_relative, window=None)` | `bool` | Accepts an absolute path or a relative resource path. |
| `get_resource` | `get_resource(*segments, required=True)` | `str` | Resolves a resource to an absolute path string. |
| `run` | `run()` | `int` | Starts the event loop through the active framework adapter. |

### Component (`qyro.ui.component`)

Component is a lifecycle mixin designed for UI classes supporting multi-toolkit frameworks.

#### Instantiation & Props

Components can receive properties (`props`) in two ways upon instantiation:

1. Via an explicit dictionary: `MyComponent(parent=self, props={"title": "Hello"})`
2. Via direct keyword arguments: `MyComponent(parent=self, title="Hello")` (automatically isolating toolkit-specific arguments like `parent`).

Lifecycle hook order:

1. `component_will_mount`
2. `render`
3. `component_did_mount`
4. `set_styles`
5. `on_resize`

Primary hooks:

| Hook | Signature | Purpose |
|---|---|---|
| `component_will_mount` | `component_will_mount()` | Performs initialization before rendering. |
| `render` | `render()` | Builds the component's widgets and layouts. |
| `component_did_mount` | `component_did_mount()` | Performs setup after rendering. |
| `set_styles` | `set_styles(path_or_styles=None)` | Applies a stylesheet from a file path or an inline style definition. |
| `on_resize` | `on_resize()` | Handles responsive behavior when the component is mounted or resized. |


Utility methods:

| Method | Signature | Description |
| --- | --- | --- |
| `calc` | `calc(a, b)` | Returns a percentage-based integer value. |
| `find` | `find(target_type, name="")` | Delegates to the native `findChild` when available. |
| `destroy_component` | `destroy_component()` | Detaches and schedules widget cleanup safely. |
| `get_resource` | `get_resource(*segments, required=True)` | Top-level resource resolver shortcut. |



* Automatic icon/title assignment is best-effort and depends on toolkit capabilities and available files.

## Repository pointers

* Public entrypoint: qyro/**init**.py
* Application context facade: qyro/client/context.py
* Component lifecycle mixin: qyro/client/component.py
* Framework adapters: qyro/adapters/frameworks/
* Resource resolver: qyro/adapters/resources/filesystem_resources.py
* Settings loader: qyro/adapters/settings/json_settings.py

## 🤝 Contributing

Contributions to `qyro` and the Qyro ecosystem are welcome.

1. Fork the repository on GitHub.
2. Create your feature branch (`git checkout -b feature/amazing-feature`).
3. Run test suites (`poetry run pytest`).
4. Commit your changes (`git commit -m 'feat: add amazing feature'`).
5. Push to your branch (`git push origin feature/amazing-feature`).
6. Open a Pull Request.

---

## 📄 License

MIT. See [LICENSE](LICENSE).

---

## 👥 Organization & Maintainers

- **Organization:** [Neuri](https://github.com/Neuri-AI)
- **Lead Maintainer:** Luis Alfredo De Los Reyes ([luisalfredoreyes98@gmail.com](mailto:luisalfredoreyes98@gmail.com))
- **Ecosystem:** [Qyro](https://github.com/Neuri-AI/qyro) • [Qyro CLI](https://github.com/Neuri-AI/qyro-cli) • [Boilerplates](https://github.com/Neuri-AI)
