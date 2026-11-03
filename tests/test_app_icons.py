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
