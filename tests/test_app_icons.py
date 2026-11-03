"""Platform-specific application icon selection and native Tk presentation."""

from pathlib import Path
import sys
import types

import pytest

from qyro.client.velto_context import VeltoContext
from qyro.domain.entities import PlatformType


class _ResourceResolver:
    def __init__(self, available):
        self.available = available

    def execute(self, *segments, required=False):
        return self.available.get("/".join(segments), Path("/nonexistent/qyro_icon"))


class _Context:
    get_app_icon_path = VeltoContext.get_app_icon_path

    def __init__(self, platform, available, config=None):
        self.platform = platform
        self.app_settings = config or {}
        self.container = types.SimpleNamespace(
            resolve_resource_use_case=_ResourceResolver(available),
        )


@pytest.mark.parametrize(("platform", "expected"), [
    (PlatformType.MACOS, "icons/256.png"),
    (PlatformType.LINUX, "icons/256.png"),
    (PlatformType.WINDOWS, "icons/Icon.ico"),
])
def test_boilerplate_icon_prefers_platform_format(tmp_path, platform, expected):
    candidates = {}
    for name in ("icons/Icon.ico", "icons/256.png", "icons/64.png"):
        path = tmp_path / name.rsplit("/", 1)[-1]
        path.write_bytes(b"test")
        candidates[name] = path

    context = _Context(platform, candidates)
    assert context.get_app_icon_path() == str(candidates[expected])


def test_mac_uses_fallback_png_not_windows_ico(tmp_path):
    image = tmp_path / "64.png"
    image.write_bytes(b"test")
    ico = tmp_path / "Icon.ico"
    ico.write_bytes(b"test")
    context = _Context(PlatformType.MACOS, {
        "icons/Icon.ico": ico, "icons/64.png": image,
    })
    assert context.get_app_icon_path() == str(image)


def test_explicit_icon_has_priority(tmp_path):
    custom = tmp_path / "custom.png"
    custom.write_bytes(b"test")
    standard = tmp_path / "256.png"
    standard.write_bytes(b"test")
    context = _Context(PlatformType.MACOS, {
        "branding/custom.png": custom,
        "icons/256.png": standard,
    }, {"icon": "branding/custom.png"})
    assert context.get_app_icon_path() == str(custom)


def test_tk_png_icon_is_loaded_and_kept_alive(monkeypatch, tmp_path):
    image = tmp_path / "icon.png"
    image.write_bytes(b"test")
    events = []
    photo = object()
    monkeypatch.setitem(sys.modules, "tkinter", types.SimpleNamespace(
        PhotoImage=lambda *, file: (events.append(("photo", file)), photo)[-1],
    ))
    monkeypatch.setattr(sys, "platform", "darwin")
    root = types.SimpleNamespace(
        iconphoto=lambda default, value: events.append(("iconphoto", default, value)),
        iconbitmap=lambda path: events.append(("iconbitmap", path)),
    )
    VeltoContext._apply_tk_icon(root, str(image))
    assert events == [("photo", str(image)), ("iconphoto", True, photo)]
    assert root._qyro_icon_photo is photo


def test_tk_icon_failures_are_visible(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setitem(sys.modules, "tkinter", types.SimpleNamespace(
        PhotoImage=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("bad PNG")),
    ))
    root = types.SimpleNamespace(iconphoto=lambda *_: None)
    with pytest.warns(RuntimeWarning, match="Could not apply Tkinter application icon"):
        VeltoContext._apply_tk_icon(root, "bad.png")


def test_kivy_macos_presentation_updates_sdl_and_dock(monkeypatch, tmp_path):
    from qyro.client import macos_dock_icon

    icon = tmp_path / "256.png"
    icon.write_bytes(b"test")
    events = []
    class Window:
        title = None

        @classmethod
        def set_icon(cls, filename):
            events.append(("sdl_icon", filename))

    window_module = types.ModuleType("kivy.core.window")
    window_module.Window = Window
    monkeypatch.setitem(sys.modules, "kivy", types.ModuleType("kivy"))
    monkeypatch.setitem(sys.modules, "kivy.core", types.ModuleType("kivy.core"))
    monkeypatch.setitem(sys.modules, "kivy.core.window", window_module)
    monkeypatch.setattr(macos_dock_icon, "set_macos_dock_icon",
                        lambda filename: events.append(("dock_icon", filename)) or True)
    ctx = _Context(PlatformType.MACOS, {"icons/256.png": icon})
    ctx.metadata = types.SimpleNamespace(app_name="Velto Test")
    ctx._handle = object()
    VeltoContext._present(ctx, "kivy", 800, 600)
    assert Window.title == "Velto Test"
    assert events == [("sdl_icon", str(icon)), ("dock_icon", str(icon))]


def test_macos_dock_icon_is_noop_on_linux(monkeypatch):
    from qyro.client.macos_dock_icon import set_macos_dock_icon

    monkeypatch.setattr(sys, "platform", "linux")
    assert not set_macos_dock_icon("/tmp/icon.png")


def test_macos_dock_icon_missing_file_warns(monkeypatch):
    from qyro.client.macos_dock_icon import set_macos_dock_icon

    monkeypatch.setattr(sys, "platform", "darwin")
    with pytest.warns(RuntimeWarning, match="does not exist"):
        assert not set_macos_dock_icon("/nonexistent/velto.png")
