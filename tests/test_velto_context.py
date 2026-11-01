from __future__ import annotations

import sys
from contextlib import nullcontext
import types
from pathlib import Path
from typing import Any

import pytest

from qyro.client.velto_context import VeltoContext
from qyro.domain.entities import AppMetadata, ExecutionMode, PlatformType
from qyro.domain.errors import FrameworkNotAvailableError


class _Resources:
    def __init__(self, mapping: dict[str, Path] | None = None) -> None:
        self.mapping = mapping or {}

    def execute(self, *segments: str, required: bool = True) -> Path:
        value = self.mapping.get("/".join(segments), Path("__missing__"))
        if required and not value.exists():
            raise FileNotFoundError(segments)
        return value


class _Container:
    def __init__(self, mapping: dict[str, Path] | None = None) -> None:
        self.resolve_resource_use_case = _Resources(mapping)


class _Renderer:
    def __init__(self) -> None:
        self.run_calls = 0

    def run(self) -> int:
        self.run_calls += 1
        return 23


class _Handle:
    widget = object()


class _App:
    instances: list["_App"] = []

    def __init__(self, root: object, *, renderer: object) -> None:
        self.root = root
        self.renderer = renderer
        self.mount_calls = 0
        self.unmount_calls = 0
        self.__class__.instances.append(self)

    def mount(self) -> _Handle:
        self.mount_calls += 1
        return _Handle()

    def unmount(self) -> None:
        self.unmount_calls += 1


@pytest.fixture(autouse=True)
def reset_context(monkeypatch: pytest.MonkeyPatch) -> None:
    VeltoContext._global_container = None
    VeltoContext._global_boot_info = None
    _App.instances.clear()
    psx = types.ModuleType("psx")
    psx.__path__ = []
    psx.App = _App
    psx.component = lambda fn: fn
    monkeypatch.setitem(sys.modules, "psx", psx)
    monkeypatch.setitem(sys.modules, "psx.css", types.ModuleType("psx.css"))
    monkeypatch.setitem(sys.modules, "psx.css.context", types.SimpleNamespace(
        scoped_css_resources=lambda *a, **kw: nullcontext()))
    monkeypatch.setitem(
        sys.modules,
        "psx.markup.component_compiler",
        types.SimpleNamespace(compile_component=lambda fn: fn),
    )
    yield
    VeltoContext._global_container = None
    VeltoContext._global_boot_info = None


def bind_context(settings: dict[str, Any], mapping: dict[str, Path] | None = None) -> None:
    VeltoContext._global_container = _Container(mapping)  # type: ignore[assignment]
    VeltoContext._global_boot_info = {
        "metadata": AppMetadata(app_name="Velto Test", raw_settings=settings),
        "is_frozen": True,
        "platform": PlatformType.LINUX,
        "execution_mode": ExecutionMode.FROZEN_GENERIC,
    }


class _Example(VeltoContext):
    def __init__(self) -> None:
        super().__init__()
        self.render_calls = 0

    def render(self) -> object:
        self.render_calls += 1
        return "root-vnode"


class _Store:
    def get_state(self) -> object:
        return {}

    def dispatch(self, action: object) -> object:
        return action

    def select(self, **_: object) -> object:
        return lambda: None


@pytest.mark.parametrize(
    ("window", "expected"),
    [
        ({"width": 640, "height": 480}, (640, 480)),
        (None, (800, 600)),
        ({"width": 640}, (800, 600)),
        ({"width": True, "height": 480}, (800, 600)),
        ({"width": 0, "height": 480}, (800, 600)),
        ({"width": -1, "height": 480}, (800, 600)),
        ({"width": "640", "height": 480}, (800, 600)),
    ],
)
def test_window_size_is_deterministic(window: object, expected: tuple[int, int]) -> None:
    settings = {} if window is None else {"window": window}
    assert VeltoContext._window_size(settings) == expected


@pytest.mark.parametrize("binding", ["PySide6", "PySide2", "PyQt6", "PyQt5", "Kivy", "Tkinter"])
def test_binding_is_case_insensitive(binding: str) -> None:
    assert VeltoContext._binding({"binding": binding}) == binding.lower()


def test_framework_prefers_framework_over_binding() -> None:
    assert VeltoContext._binding({"binding": "Kivy", "framework": "Tkinter"}) == "tkinter"


def test_invalid_binding_has_supported_renderer_hint() -> None:
    context = _Example.__new__(_Example)
    with pytest.raises(FrameworkNotAvailableError, match="Velto supports"):
        context._create_renderer("unknown", 800, 600)


def test_mount_run_and_unmount_delegate_to_velto(monkeypatch: pytest.MonkeyPatch) -> None:
    bind_context({"binding": "headless", "window": {"width": 640, "height": 480}})
    renderer = _Renderer()
    monkeypatch.setattr(_Example, "_create_renderer", lambda *_: renderer)
    monkeypatch.setattr(_Example, "_present", lambda *_: None)
    context = _Example()

    assert context.run() == 23
    assert context.render_calls == 1
    assert context.app is _App.instances[0]
    assert context.app.root == "root-vnode"
    assert context.renderer is renderer
    assert context.handle is not None
    assert context.mount() is context.handle
    assert _App.instances[0].mount_calls == 1

    context.unmount()
    assert _App.instances[0].unmount_calls == 1
    assert context.handle is None


def test_context_automatically_provides_the_single_module_pydux_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _Store()
    renderer = _Renderer()
    monkeypatch.setitem(_Example.render.__globals__, "demo_store", store)
    monkeypatch.setitem(
        sys.modules,
        "pydux",
        types.SimpleNamespace(StoreProvider=lambda provided, child: ("provider", provided, child)),
    )
    bind_context({"framework": "headless"})
    monkeypatch.setattr(_Example, "_create_renderer", lambda *_: renderer)
    monkeypatch.setattr(_Example, "_present", lambda *_: None)

    _Example().mount()

    root = _App.instances[0].root
    assert root[0] == "provider"
    assert root[1] is store
    monkeypatch.delitem(_Example.render.__globals__, "demo_store")


def test_context_requires_an_explicit_store_when_the_module_has_multiple(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(_Example.render.__globals__, "first_store", _Store())
    monkeypatch.setitem(_Example.render.__globals__, "second_store", _Store())
    with pytest.raises(RuntimeError, match="More than one Pydux store"):
        _Example()._pydux_store()
    monkeypatch.delitem(_Example.render.__globals__, "first_store")
    monkeypatch.delitem(_Example.render.__globals__, "second_store")


def test_qt_presentation_uses_the_host_window() -> None:
    class _Window:
        def __init__(self) -> None:
            self.size: tuple[int, int] | None = None
            self.title = ""
            self.shown = False

        def resize(self, width: int, height: int) -> None:
            self.size = (width, height)

        def setWindowTitle(self, title: str) -> None:
            self.title = title

        def show(self) -> None:
            self.shown = True

    class _RootWidget:
        def __init__(self, window: _Window) -> None:
            self._window = window

        def window(self) -> _Window:
            return self._window

    bind_context({"framework": "PySide6"})
    context = _Example()
    window = _Window()
    context._handle = types.SimpleNamespace(widget=_RootWidget(window))
    context._renderer = types.SimpleNamespace(application=object())

    context._present("pyside6", 640, 480)

    assert window.size == (640, 480)
    assert window.title == "Velto Test"
    assert window.shown is True


def test_context_exposes_runtime_and_resource_helpers(tmp_path: Path) -> None:
    icon = tmp_path / "icon.png"
    icon.write_text("fake", encoding="utf-8")
    bind_context({"binding": "Tkinter", "icon": "icons/app.png"}, {"icons/app.png": icon})
    context = _Example()

    assert context.app_settings["binding"] == "Tkinter"
    assert context.is_frozen is True
    assert context.platform is PlatformType.LINUX
    assert context.execution_mode is ExecutionMode.FROZEN_GENERIC
    assert context.get_app_icon_path() == str(icon)
    assert context.get_resource("icons", "app.png") == str(icon)


def test_legacy_ui_symbols_are_not_public() -> None:
    import qyro

    assert not hasattr(qyro, "Component")
    assert not hasattr(qyro, "ApplicationContext")


@pytest.mark.parametrize(
    ("requested", "drawable"),
    [
        ((800, 600), (1600, 1200)),
        ((1600, 1200), (3200, 2400)),
    ],
)
def test_kivy_retina_window_size_is_configured_once_before_psx_mount(
    monkeypatch: pytest.MonkeyPatch,
    requested: tuple[int, int],
    drawable: tuple[int, int],
) -> None:
    """Window points, Retina drawables, and SFLE viewport stay distinct."""
    # The source-level lifecycle test is independent of the CI host's screen.
    from qyro.client import kivy_window_geometry
    monkeypatch.setattr(
        kivy_window_geometry, "visible_kivy_window_size", lambda size: size,
    )
    events: list[tuple[object, ...]] = []
    bind_context({"framework": "Kivy"})
    context = _Example()

    kivy = types.ModuleType("kivy")
    kivy.__path__ = []
    core = types.ModuleType("kivy.core")
    core.__path__ = []
    config = types.ModuleType("kivy.config")
    config.Config = types.SimpleNamespace(
        set=lambda section, key, value: events.append(
            ("config", section, key, value)
        )
    )

    class WindowProbe:
        size = drawable
        title = ""
        icon = ""

        def __init__(self) -> None:
            self.system_size = (1920, 1080)

        def __setattr__(self, name: str, value: object) -> None:
            if name == "system_size":
                events.append(("system_size", value))
            if name == "size":
                raise AssertionError("Qyro must not write drawable Window.size")
            super().__setattr__(name, value)

    window = WindowProbe()
    events.clear()
    window_module = types.ModuleType("kivy.core.window")
    window_module.Window = window

    sfle = types.ModuleType("psx.sfle")
    sfle.__path__ = []
    model = types.ModuleType("psx.sfle.model")

    class AvailableSize:
        def __init__(self, value, definite=False):
            self.value = value
            self.definite = definite

    class LayoutConstraints:
        def __init__(self, width, height):
            self.width = width
            self.height = height

    model.AvailableSize = AvailableSize
    model.LayoutConstraints = LayoutConstraints
    renderers = types.ModuleType("psx.renderers")
    renderers.__path__ = []
    renderer_module = types.ModuleType("psx.renderers.kivy")

    class RendererProbe:
        def __init__(self, *, sfle_constraints):
            events.append(("renderer",))
            self.sfle_constraints = sfle_constraints

    renderer_module.KivyRenderer = RendererProbe
    for name, module in (
        ("kivy", kivy), ("kivy.config", config), ("kivy.core", core),
        ("kivy.core.window", window_module), ("psx.sfle", sfle),
        ("psx.sfle.model", model), ("psx.renderers", renderers),
        ("psx.renderers.kivy", renderer_module),
    ):
        monkeypatch.setitem(sys.modules, name, module)

    renderer = context._create_renderer("kivy", *requested)
    assert events == [
        ("config", "graphics", "width", str(requested[0])),
        ("config", "graphics", "height", str(requested[1])),
        ("config", "graphics", "position", "auto"),
        ("renderer",),
    ]
    assert window.system_size == (1920, 1080)
    assert window.size == drawable
    assert renderer.sfle_constraints.width.value == drawable[0]
    assert renderer.sfle_constraints.height.value == drawable[1]

    # Present may set title/icon, but must never resize the live Kivy
    # window while PSX's interactive widget tree is already mounted.
    context._present("kivy", *requested)
    assert window.title == "Velto Test"
    assert window.size == drawable
    assert not any(entry[0] == "system_size" for entry in events)
