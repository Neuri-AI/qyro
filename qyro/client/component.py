"""
Qyro Component Module.

Provides a React-inspired component lifecycle architecture for Qt/PySide
and desktop GUI widgets.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional, TypeVar

T = TypeVar("T")


class Component:
    """
    Base class, mixin, and decorator for Qyro GUI components.

    Inspired by React class components and adapted for Qt bindings including
    PySide6, PyQt6, PySide2, and PyQt5.

    Components can be declared either by inheritance:

        class MyWidget(QWidget, Component):
            ...

    or by using `Component` as a class decorator:

        @Component
        class MyWidget(QWidget):
            ...

    The component lifecycle is responsible for widget-level UI initialization,
    rendering, styling, and responsive behavior. Application-level lifecycle
    management remains the responsibility of ApplicationContext.

    The lifecycle executes in the following order:

    1. Initialize the component and its underlying Qt widget.
    2. Call `component_will_mount()`.
    3. Render the component through `render()` or `render_()`.
    4. Call `component_did_mount()`.
    5. Apply component styles through `set_styles()`.
    6. Perform the initial responsive layout through `on_resize()`.
    7. Recalculate responsive layout whenever the widget is resized.
    """

    def __new__(
        cls,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Creates a component instance or decorates a widget class.

        When `Component` itself is called with a class, it is used as a
        class decorator. Subclasses of `Component` retain normal instance
        construction behavior.
        """
        if cls is Component and args and isinstance(args[0], type):
            return cls._decorate(args[0])

        return super().__new__(cls)

    @classmethod
    def _decorate(cls, target: type[T]) -> type[T]:
        """
        Converts a regular widget class into a Qyro component.

        The returned class inherits from both the original widget class and
        `Component`, preserving the original class API while adding the
        complete component lifecycle.
        """
        if issubclass(target, Component):
            return target

        component = type(
            target.__name__,
            (target, Component),
            {
                "__module__": target.__module__,
                "__qualname__": target.__qualname__,
                "__doc__": target.__doc__,
            },
        )

        return component

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Wraps subclass initialization and resize handling.

        The constructor wrapper mounts the component lifecycle after the
        subclass and its underlying Qt widget have been initialized.

        The resize wrapper ensures that responsive behavior is triggered
        regardless of the method resolution order of the subclass.
        """
        super().__init_subclass__(**kwargs)

        orig_init = cls.__init__

        if not getattr(orig_init, "_qyro_component_wrapped", False):

            def wrapped_init(
                self: Any,
                *args: Any,
                **kwargs: Any,
            ) -> None:
                """Initialize the component and mount its lifecycle."""
                # Support explicit props dictionary keyword argument
                if "props" in kwargs:
                    explicit_props = kwargs.pop("props")
                    if isinstance(explicit_props, dict):
                        self.props.update(explicit_props)

                # Separate Qt-specific arguments (like parent) from prop shortcuts
                qt_kwargs = {}
                if "parent" in kwargs:
                    qt_kwargs["parent"] = kwargs.pop("parent")

                # Any remaining keyword arguments become props directly
                if kwargs:
                    self.props.update(kwargs)

                # Initialize the underlying Qt widget safely
                orig_init(self, *args, **qt_kwargs)

                if not getattr(
                    self,
                    "_component_lifecycle_mounted",
                    False,
                ):
                    self._mount_component_lifecycle()

            wrapped_init._qyro_component_wrapped = True
            cls.__init__ = wrapped_init

        orig_resize = getattr(cls, "resizeEvent", None)

        if not getattr(orig_resize, "_qyro_resize_wrapped", False):

            def wrapped_resize(
                self: Any,
                event: Any = None,
            ) -> None:
                """
                Updates responsive layout and forwards the resize event.

                The original resize handler is called after the component's
                responsive handler when one is available.
                """
                self._call_first(
                    "on_resize",
                    "on_resize",
                )

                if (
                    orig_resize
                    and callable(orig_resize)
                    and orig_resize != wrapped_resize
                ):
                    try:
                        orig_resize(self, event)
                    except Exception:
                        pass

            wrapped_resize._qyro_resize_wrapped = True
            cls.resizeEvent = wrapped_resize

    def _call_first(self, *names: str) -> None:
        """
        Calls the first available callable from the given method names.

        Method names are checked in the order provided, allowing legacy
        aliases to remain supported without duplicating lifecycle logic.
        """
        for name in names:
            method = getattr(self, name, None)

            if callable(method):
                method()
                return

    def _mount_component_lifecycle(self) -> None:
        """
        Mounts the component and executes its complete lifecycle.

        Hooks are resolved in declaration order, with the first available
        method used when multiple names represent the same lifecycle stage.
        """
        self._component_lifecycle_mounted = True

        # Enables styled backgrounds automatically before rendering
        self._allow_styled_background()

        lifecycle = (
            ("component_will_mount",),
            ("render", "render_"),
            ("component_did_mount",),
            ("set_styles",),
            ("on_resize",),
        )

        for hooks in lifecycle:
            self._call_first(*hooks)

    def component_will_mount(self) -> None:
        """Called immediately before the component UI is rendered."""
        pass

    def _allow_styled_background(self) -> None:
        """
        Enables Qt's styled background attribute on the component.

        The active Qt binding is detected from the component's MRO and loaded
        modules. This allows stylesheets to correctly render backgrounds,
        borders, and border radii on custom QWidget subclasses.
        """
        if not hasattr(self, "setAttribute"):
            return

        qt_attr = None
        active_pkgs = []

        for cls in getattr(type(self), "__mro__", []):
            module = getattr(cls, "__module__", "")

            if module:
                package = module.split(".")[0]

                if (
                    package in (
                        "PyQt5",
                        "PySide6",
                        "PyQt6",
                        "PySide2",
                    )
                    and package not in active_pkgs
                ):
                    active_pkgs.append(package)

        for package in (
            "PyQt5",
            "PySide6",
            "PyQt6",
            "PySide2",
        ):
            if (
                f"{package}.QtCore" in sys.modules
                or package in sys.modules
            ) and package not in active_pkgs:
                active_pkgs.append(package)

        candidates = (
            [f"{package}.QtCore" for package in active_pkgs]
            if active_pkgs
            else [
                "PySide6.QtCore",
                "PyQt6.QtCore",
                "PySide2.QtCore",
                "PyQt5.QtCore",
            ]
        )

        for module_name in candidates:
            try:
                module = __import__(
                    module_name,
                    fromlist=["Qt"],
                )
                qt = getattr(module, "Qt", None)

                if qt is not None:
                    if hasattr(qt, "WidgetAttribute") and hasattr(
                        qt.WidgetAttribute,
                        "WA_StyledBackground",
                    ):
                        qt_attr = qt.WidgetAttribute.WA_StyledBackground
                    elif hasattr(qt, "WA_StyledBackground"):
                        qt_attr = qt.WA_StyledBackground

                if qt_attr is not None:
                    break
            except ImportError:
                continue

        if qt_attr is not None:
            try:
                self.setAttribute(qt_attr, True)
            except Exception:
                pass

    def render(self) -> None:
        """
        Constructs the component's child widgets, layouts, and connections.

        Subclasses should override this method to define their UI structure.
        """
        pass

    def render_(self) -> None:
        """Backward-compatible alias for `render()`."""
        pass

    def component_did_mount(self) -> None:
        """Called immediately after the component UI has been mounted."""
        pass

    def set_styles(
        self,
        path_or_styles: Optional[str] = None,
    ) -> None:
        """
        Applies styles or a stylesheet to the component.

        `path_or_styles` may contain an inline stylesheet string, a relative resource
        path, or an absolute filesystem path.

        When `path_or_styles` is `None`, the component's `STYLES`, `CSS` or
        `STYLESHEET` attribute is used instead.

        Filesystem paths are resolved first, followed by Qyro resources.
        Unresolved values are treated as inline styles.
        """
        if not hasattr(self, "setStyleSheet"):
            return

        content = path_or_styles

        if content is None:
            content = (
                getattr(self, "STYLES", None)
                or getattr(self, "CSS", None)
                or getattr(self, "STYLESHEET", None)
            )

        if not content or not isinstance(content, str):
            return

        stylesheet_text = None
        direct_path = Path(content)

        if direct_path.exists() and direct_path.is_file():
            try:
                stylesheet_text = direct_path.read_text(
                    encoding="utf-8",
                )
            except Exception:
                pass

        if stylesheet_text is None and not (
            "{" in content or ";" in content
        ):
            try:
                segments = [
                    segment
                    for segment in content.replace(
                        "\\",
                        "/",
                    ).split("/")
                    if segment
                ]

                resolved = self.get_resource(
                    *segments,
                    required=False,
                )
                resolved_path = Path(resolved)

                if resolved_path.exists() and resolved_path.is_file():
                    stylesheet_text = resolved_path.read_text(
                        encoding="utf-8",
                    )
            except Exception:
                pass

        if stylesheet_text is None:
            stylesheet_text = content

        try:
            self.setStyleSheet(stylesheet_text)
        except Exception:
            pass

    def on_resize(self) -> None:
        """
        Updates the component layout according to its current dimensions.

        Subclasses can override this method to implement responsive behavior.
        It is called during mounting and whenever the widget is resized.
        """
        pass

    def resizeEvent(self, event: Any = None) -> None:
        """
        Handles Qt resize events and updates the responsive layout.

        The event is forwarded to the next `resizeEvent` implementation in
        the method resolution order when one is available.
        """
        self._call_first("on_resize")

        base_resize = getattr(
            super(),
            "resizeEvent",
            None,
        )

        if callable(base_resize):
            try:
                base_resize(event)
            except Exception:
                pass

    def destroy_component(self) -> None:
        """
        Detaches the component from its parent and schedules its deletion.

        Both operations are performed only when supported by the underlying
        widget implementation.
        """
        if hasattr(self, "setParent"):
            try:
                self.setParent(None)
            except Exception:
                pass

        if hasattr(self, "deleteLater"):
            try:
                self.deleteLater()
            except Exception:
                pass

    def destroyComponent(self) -> None:
        """Backward-compatible alias for `destroy_component()`."""
        self.destroy_component()

    def find(
        self,
        target_type: Any,
        name: str = "",
    ) -> Any:
        """
        Finds a child widget by type and optional object name.

        Delegates the lookup to Qt's `findChild` implementation when
        available.
        """
        find_child = getattr(
            self,
            "findChild",
            None,
        )

        if callable(find_child):
            return find_child(target_type, name)

        return None

    @staticmethod
    def calc(
        a: float | int,
        b: float | int,
    ) -> int:
        """
        Calculates a percentage-based dimension.

        The result is equivalent to `int((a * b) / 100.0)` and is intended
        for responsive layout calculations.

        Example:
            width = `self.calc(self.width(), 50)`
        """
        return int((float(a) * float(b)) / 100.0)

    def get_resource(
        self,
        *segments: str,
        required: bool = True,
    ) -> str:
        """
        Resolves resource path segments through the Qyro engine.

        Returns the resolved absolute path as a string.
        """
        container = getattr(self, "_container", None)
        if container is not None:
            return str(container.resolve_resource_use_case.execute(*segments, required=required))

        import qyro

        return qyro.get_resource(*segments, required=required)

    @property
    def app_settings(self) -> dict[str, Any]:
        """Returns the application's build settings."""
        container = getattr(self, "_container", None)
        if container is not None:
            return container.load_settings_use_case.execute().raw_settings

        import qyro

        return qyro.load_build_settings()

    @property
    def is_frozen(self) -> bool:
        """Returns whether the application is running as a frozen executable."""
        container = getattr(self, "_container", None)
        if container is not None:
            return container.env_adapter.is_frozen()

        import qyro

        return qyro.is_frozen()

    @property
    def props(self) -> dict[str, Any]:
        """
        Returns the component properties.

        An empty dictionary is created when no properties have been assigned.
        """
        if not hasattr(self, "_props"):
            self._props = {}

        return self._props

    @props.setter
    def props(
        self,
        value: dict[str, Any],
    ) -> None:
        """Sets the component properties."""
        self._props = value


PPGLifeCycle = Component