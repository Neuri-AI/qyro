from __future__ import annotations

from pathlib import Path
from typing import Any

from qyro.client.component import Component


def test_component_as_decorator_returns_component_subclass() -> None:
    class _Widget:
        pass

    decorated = Component(_Widget)

    assert issubclass(decorated, _Widget)
    assert issubclass(decorated, Component)


def test_component_lifecycle_mount_order_and_single_mount() -> None:
    class _Sample(Component):
        def __init__(self, parent: Any = None) -> None:
            self.parent_seen = parent
            self.calls: list[str] = []

        def component_will_mount(self) -> None:
            self.calls.append("will")

        def render(self) -> None:
            self.calls.append("render")

        def component_did_mount(self) -> None:
            self.calls.append("did")

        def set_styles(self, path_or_styles: str | None = None) -> None:
            self.calls.append("styles")

        def on_resize(self) -> None:
            self.calls.append("resize")

    sample = _Sample(parent="parent-id")

    assert sample.parent_seen == "parent-id"
    assert sample.calls == ["will", "render", "did", "styles", "resize"]


def test_component_props_merge_from_kwargs_and_props_dict() -> None:
    class _Sample(Component):
        def __init__(self, parent: Any = None) -> None:
            self.parent_seen = parent

    sample = _Sample(parent="root", props={"b": 2}, a=1)

    assert sample.parent_seen == "root"
    assert sample.props == {"a": 1, "b": 2}


def test_set_styles_accepts_inline_styles() -> None:
    class _Styled(Component):
        def __init__(self) -> None:
            self.last_stylesheet = None

        def setStyleSheet(self, css: str) -> None:
            self.last_stylesheet = css

    styled = _Styled()
    styled.set_styles("QWidget { color: red; }")

    assert styled.last_stylesheet == "QWidget { color: red; }"


def test_set_styles_reads_file_content(tmp_path: Path) -> None:
    css_file = tmp_path / "theme.css"
    css_file.write_text("QLabel { font-size: 14px; }", encoding="utf-8")

    class _Styled(Component):
        def __init__(self) -> None:
            self.last_stylesheet = None

        def setStyleSheet(self, css: str) -> None:
            self.last_stylesheet = css

    styled = _Styled()
    styled.set_styles(str(css_file))

    assert styled.last_stylesheet == "QLabel { font-size: 14px; }"


def test_find_returns_none_without_findChild() -> None:
    class _Sample(Component):
        pass

    sample = _Sample()

    assert sample.find(object, "name") is None


def test_calc_returns_percentage_int() -> None:
    assert Component.calc(300, 25) == 75
    assert Component.calc(5.5, 50) == 2


def test_destroy_component_calls_supported_methods() -> None:
    class _Sample(Component):
        def __init__(self) -> None:
            self.parent = object()
            self.deleted = False

        def setParent(self, parent: Any) -> None:
            self.parent = parent

        def deleteLater(self) -> None:
            self.deleted = True

    sample = _Sample()
    sample.destroy_component()

    assert sample.parent is None
    assert sample.deleted is True
