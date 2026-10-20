"""Release VeltoContext resolves global CSS via its existing resource contract."""
from contextlib import contextmanager
from pathlib import Path
import sys
import types

from qyro.client.velto_context import VeltoContext


def test_global_css_scope_uses_resolved_assets_and_preserves_render(tmp_path, monkeypatch):
    css_path = tmp_path / "app.css"
    css_path.write_text("div {color:#fff}", encoding="utf8")
    captured = []

    @contextmanager
    def scoped(stylesheets, *, resolver):
        captured.append(tuple(stylesheets))
        captured.append(resolver("app.css"))
        yield

    module = types.ModuleType("psx.css.context")
    module.scoped_css_resources = scoped
    monkeypatch.setitem(sys.modules, "psx.css.context", module)

    class Example(VeltoContext):
        stylesheets = ["app.css"]
        def render(self):
            return "view"

    instance = object.__new__(Example)
    instance.get_resource = lambda name: str(tmp_path / name)
    instance._metadata = None
    instance._compiled = None
    # Avoid running the native engine; inspect the component wrapper.
    # Fake compile_component/component to invoke the root callable in isolation.
    psx = types.ModuleType("psx")
    psx.__path__ = []
    psx.component = lambda value: value
    markup = types.ModuleType("psx.markup")
    markup.__path__ = []
    compiler = types.ModuleType("psx.markup.component_compiler")
    compiler.compile_component = lambda value: value
    monkeypatch.setitem(sys.modules, "psx", psx)
    monkeypatch.setitem(sys.modules, "psx.markup", markup)
    monkeypatch.setitem(sys.modules, "psx.markup.component_compiler", compiler)
    monkeypatch.setattr(Example, "app_settings", property(lambda _: {"css": {"stylesheets": ["reset.css"]}}))
    root = instance._root_component()
    assert root() == "view"
    assert captured == [("reset.css", "app.css"), b"div {color:#fff}"]
