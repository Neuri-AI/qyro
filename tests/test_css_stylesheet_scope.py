"""VeltoContext stylesheet declarations do not change its initialization lifecycle."""
from contextlib import contextmanager
from pathlib import Path
import sys
import types

from qyro.client.context import ApplicationContext


def test_class_level_stylesheets_scope_render_without_init_override(monkeypatch, tmp_path):
    css = tmp_path / "app.css"
    css.write_text("div {color: #fff}", encoding="utf-8")
    observed = []

    @contextmanager
    def scope(paths, *, resolver):
        observed.append(("paths", tuple(paths)))
        observed.append(("bytes", resolver("app.css")))
        yield
        observed.append(("released", True))

    psx = types.ModuleType("psx")
    package = types.ModuleType("psx.css")
    package.__path__ = []
    module = types.ModuleType("psx.css.context")
    module.scoped_css_resources = scope
    monkeypatch.setitem(sys.modules, "psx", psx)
    monkeypatch.setitem(sys.modules, "psx.css", package)
    monkeypatch.setitem(sys.modules, "psx.css.context", module)

    class Demo(ApplicationContext):
        stylesheets = ["app.css"]

        def get_resource(self, path):
            return str(tmp_path / path)

        def render(self):
            observed.append(("render", True))
            return "ready"

    # Bypass Qyro's native engine startup: only test the render wrapper.
    instance = object.__new__(Demo)
    assert Demo.render(instance) == "ready"
    assert observed == [
        ("paths", ("app.css",)),
        ("bytes", b"div {color: #fff}"),
        ("render", True),
        ("released", True),
    ]
