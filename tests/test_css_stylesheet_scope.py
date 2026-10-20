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


def test_project_settings_precede_class_stylesheets(monkeypatch, tmp_path):
    (tmp_path / "global.css").write_text("div {width: 10px}", encoding="utf-8")
    (tmp_path / "local.css").write_text("div {width: 20px}", encoding="utf-8")
    observed = []

    @contextmanager
    def scope(paths, *, resolver):
        observed.append(tuple(paths))
        observed.append(resolver("local.css"))
        yield

    package = types.ModuleType("psx")
    css = types.ModuleType("psx.css")
    css.__path__ = []
    module = types.ModuleType("psx.css.context")
    module.scoped_css_resources = scope
    monkeypatch.setitem(sys.modules, "psx", package)
    monkeypatch.setitem(sys.modules, "psx.css", css)
    monkeypatch.setitem(sys.modules, "psx.css.context", module)

    class Demo(ApplicationContext):
        stylesheets = ["local.css"]

        def get_resource(self, path):
            return str(tmp_path / path)

        def render(self):
            return "ready"

    settings = types.SimpleNamespace(raw_settings={"css": {"stylesheets": ["global.css"]}})
    use_case = types.SimpleNamespace(execute=lambda: settings)
    instance = object.__new__(Demo)
    instance._container = types.SimpleNamespace(load_settings_use_case=use_case)
    assert Demo.render(instance) == "ready"
    assert observed == [
        ("global.css", "local.css"),
        b"div {width: 20px}",
    ]
