<p align="center">
  <img src="https://ik.imagekit.io/kummiktgaiq/ppg/Qyro-logo.svg?updatedAt=1755215983279" alt="Qyro Logo" width="50%">
</p>

# ⚡ Qyro Runtime

> **Runtime engine for Python GUI apps with a shared application context.**


[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14%20%7C%203.15-blue.svg)](https://python.org)
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
- Hot reloading: not built into qyro.
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
    sys.exit(window.exec())

```

## Quick start (Kivy)

```python
from kivy.app import App
from kivy.uix.label import Label
from kivy.core.window import Window
from qyro import ApplicationContext
from qyro.ui.component import Component


class Kv(App, Component, ApplicationContext):

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
    app.exec()

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
* app_is_frozen (compat alias)

Function signatures:

```python
def get_resource(*segments: str, required: bool = True) -> str
def load_build_settings() -> dict
def is_frozen() -> bool

```

Behavior notes:

* get_resource returns an absolute path string.
* If required=True and a resource is not found, the resolver may raise a runtime error.
* app_is_frozen is an alias kept for compatibility.

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
| --- | --- | --- | --- |
| framework | str | None | None | Forces a specific adapter (for example: pyside6, pyqt6, kivy, tkinter, headless). |
| custom_root | Path | None | None | Overrides project root used by settings and resource resolvers. |
| enable_sentry | bool | True | Enables sentry hook only if sentry_dsn is available in loaded settings. |
| argv | list[str] | None | None | Optional argv passed to framework app creation. |

Property reference:

| Property | Type | Description |
| --- | --- | --- |
| container | EngineContainer | Underlying dependency container instance. |
| app | Any | Native framework app instance (QApplication, Tk root, Kivy app, etc.). |
| metadata | AppMetadata | App metadata object loaded from settings. |
| app_settings | dict[str, Any] | Final merged settings dictionary. |
| is_frozen | bool | True when running from a frozen bundle. |
| platform | PlatformType | Detected platform enum. |
| execution_mode | ExecutionMode | Source/frozen execution mode enum. |
| window_title | str | Current window title, with getter/setter behavior. |
| app_icon | str | None | Resolved app icon path, with setter support. |

Method reference:

| Method | Signature | Returns | Notes |
| --- | --- | --- | --- |
| get_default_window_title | `get_default_window_title()` | str | Uses metadata/app_name fallback chain. |
| get_window_title | `get_window_title()` | str | Reads current title from native window when possible. |
| set_window_title | `set_window_title(title, window=None)` | bool | Best-effort cross-toolkit title assignment. |
| get_app_icon_path | `get_app_icon_path()` | str | None | Auto-discovers icon from settings and resource conventions. |
| set_window_icon | `set_window_icon(icon_path_or_relative, window=None)` | bool | Accepts absolute path or relative resource path. |
| get_resource | `get_resource(*segments, required=True)` | str | Resolves resource to absolute path string. |
| run | `run()` | int | Starts event loop through active framework adapter. |
| exec | `exec()` | int | Compatibility runner for Qt/Tk/Kivy event loop variants. |
| exec_ | `exec_()` | int | Qt5 compatibility alias to exec(). |

### Component (`qyro.ui.component`)

Component is a lifecycle mixin designed for UI classes supporting multi-toolkit frameworks.

#### Instantiation & Props

Components can receive properties (`props`) in two ways upon instantiation:

1. Via an explicit dictionary: `MyComponent(parent=self, props={"title": "Hello"})`
2. Via direct keyword arguments: `MyComponent(parent=self, title="Hello")` (automatically isolating toolkit-specific arguments like `parent`).

Lifecycle hook order:

1. `component_will_mount`
2. `render` or `render_`
3. `component_did_mount`
4. `set_styles`
5. `on_resize`

Primary hooks:

| Hook | Signature | Purpose |
| --- | --- | --- |
| component_will_mount | `component_will_mount()` | Pre-render initialization. |
| render | `render()` | Build widgets/layouts. |
| component_did_mount | `component_did_mount()` | Post-render setup. |
| set_styles | `set_styles(path_or_styles=None)` | Apply styles/stylesheet from path or inline string. |
| on_resize | `on_resize()` | Responsive behavior on mount and resize events. |

Compatibility aliases:

* `render_`
* `destroyComponent`

Utility methods:

| Method | Signature | Description |
| --- | --- | --- |
| calc | `calc(a, b)` | Returns percentage-based integer value. |
| find | `find(target_type, name="")` | Delegates to native findChild when available. |
| destroy_component | `destroy_component()` | Detach and schedule widget cleanup safely. |
| get_resource | `get_resource(*segments, required=True)` | Top-level resource resolver shortcut. |

## Notes on compatibility

* The engine keeps several compatibility aliases from older code style:
* PPGLifeCycle -> Component
* app_is_frozen -> is_frozen helper
* exec_() alias for Qt5 style calls


* Automatic icon/title assignment is best-effort and depends on toolkit capabilities and available files.

## Repository pointers

* Public entrypoint: qyro/**init**.py
* Application context facade: qyro/client/context.py
* Component lifecycle mixin: qyro/client/component.py
* Framework adapters: qyro/adapters/frameworks/
* Resource resolver: qyro/adapters/resources/filesystem_resources.py
* Settings loader: qyro/adapters/settings/json_settings.py

## Status

Version in this repository snapshot:

* qyro 0.1.0

The package is usable today for runtime concerns, but some ecosystem features live in qyro-cli or remain outside qyro scope.
