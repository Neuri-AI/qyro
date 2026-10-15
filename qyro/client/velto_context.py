"""Velto-powered application context for Qyro.

Qyro owns configuration, resources and telemetry.  Velto owns the UI tree,
native renderer and event loop.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, Mapping, Optional

from qyro.container import EngineContainer
from qyro.domain.entities import AppMetadata, ExecutionMode, PlatformType
from qyro.domain.errors import FrameworkNotAvailableError


class VeltoContext:
    """Base class for a Velto application configured by Qyro settings.

    Subclasses implement :meth:`render` and return a PSX VNode.  The selected
    renderer comes from ``framework`` and
    uses the configured ``window`` dimensions as its SFLE viewport.
    """

    _global_container: ClassVar[Optional[EngineContainer]] = None
    _global_boot_info: ClassVar[Optional[dict[str, Any]]] = None
    _DEFAULT_WINDOW_SIZE = (800, 600)

    def __init__(
        self,
        *,
        custom_root: Path | None = None,
        enable_sentry: bool = True,
        argv: list[str] | None = None,
    ) -> None:
        self._ensure_global_engine(
            custom_root=custom_root, enable_sentry=enable_sentry, argv=argv
        )
        self._app: Any = None
        self._renderer: Any = None
        self._handle: Any = None
        self._mounted = False
        self._argv = (VeltoContext._global_boot_info or {}).get("argv")

    @classmethod
    def _ensure_global_engine(
        cls,
        *,
        custom_root: Path | None = None,
        enable_sentry: bool = True,
        argv: list[str] | None = None,
    ) -> EngineContainer:
        # Store process state on the concrete base class, not the application
        # subclass that happened to be constructed first.
        if VeltoContext._global_container is None:
            container = EngineContainer(
                custom_root=custom_root, enable_sentry=enable_sentry
            )
            VeltoContext._global_container = container
            VeltoContext._global_boot_info = container.initialize_engine_use_case.execute(argv)
        return VeltoContext._global_container

    @property
    def container(self) -> EngineContainer:
        return VeltoContext._global_container or self._ensure_global_engine()

    @property
    def metadata(self) -> AppMetadata:
        return (VeltoContext._global_boot_info or {}).get("metadata") or AppMetadata.default()

    @property
    def app_settings(self) -> dict[str, Any]:
        return self.metadata.raw_settings

    @property
    def is_frozen(self) -> bool:
        return bool((VeltoContext._global_boot_info or {}).get("is_frozen", False))

    @property
    def platform(self) -> PlatformType:
        return (VeltoContext._global_boot_info or {}).get("platform", PlatformType.UNKNOWN)

    @property
    def execution_mode(self) -> ExecutionMode:
        return (VeltoContext._global_boot_info or {}).get("execution_mode", ExecutionMode.SOURCE)

    @property
    def app(self) -> Any:
        """The mounted :class:`psx.App`, or ``None`` before mounting."""
        return self._app

    @property
    def renderer(self) -> Any:
        """The Velto renderer, created lazily while mounting."""
        return self._renderer

    @property
    def handle(self) -> Any:
        """The PSX native root handle, or ``None`` before mounting."""
        return self._handle

    def render(self) -> Any:
        """Return the root PSX VNode for this application."""
        raise NotImplementedError("VeltoContext subclasses must implement render().")

    @classmethod
    def _window_size(cls, settings: Mapping[str, Any]) -> tuple[int, int]:
        window = settings.get("window")
        if not isinstance(window, Mapping):
            return cls._DEFAULT_WINDOW_SIZE
        width, height = window.get("width"), window.get("height")
        if (
            isinstance(width, bool)
            or isinstance(height, bool)
            or not isinstance(width, int)
            or not isinstance(height, int)
            or width <= 0
            or height <= 0
        ):
            return cls._DEFAULT_WINDOW_SIZE
        return width, height

    @staticmethod
    def _binding(settings: Mapping[str, Any]) -> str:
        value = settings.get("framework") or settings.get("binding")
        if not isinstance(value, str) or not value.strip():
            raise FrameworkNotAvailableError(
                "<missing>", "Set settings/base.json 'framework' to a Velto renderer name."
            )
        return value.strip().lower()

    def _root_component(self) -> Any:
        """Wrap ``render`` in a PSX component boundary.

        Velto's compiler transforms literal ``psx(...)`` calls at component
        declaration time.  A ``VeltoContext.render`` method is not itself
        decorated, so compile the unbound method and execute it inside a small
        component boundary.  This keeps lexical expressions, f-strings and
        hooks such as ``use_state`` working in the root view.
        """
        try:
            from psx import component
            from psx.markup.component_compiler import compile_component
        except ImportError as exc:  # pragma: no cover - packaging boundary
            raise FrameworkNotAvailableError("Velto", "Install qyro-engine with Velto available.") from exc

        render_method = type(self).render
        if render_method is VeltoContext.render:
            raise NotImplementedError("VeltoContext subclasses must implement render().")
        compiled_render = compile_component(render_method)

        def root() -> Any:
            return compiled_render(self)

        root.__name__ = f"{type(self).__name__}Root"
        root.__qualname__ = root.__name__
        return component(root)

    def _create_renderer(self, binding: str, width: int, height: int) -> Any:
        supported = {"pyside6", "pyside2", "pyqt6", "pyqt5", "kivy", "tkinter"}
        if binding not in supported:
            raise FrameworkNotAvailableError(
                binding,
                "Velto supports PySide6, PySide2, PyQt6, PyQt5, Kivy, and Tkinter.",
            )
        try:
            from psx.sfle.model import AvailableSize, LayoutConstraints
        except ImportError as exc:  # pragma: no cover - packaging boundary
            raise FrameworkNotAvailableError("Velto", "Install qyro-engine with Velto available.") from exc

        constraints = LayoutConstraints(
            width=AvailableSize(width, definite=True),
            height=AvailableSize(height, definite=True),
        )
        try:
            if binding == "pyside6":
                from psx.renderers.qt.pyside import PySide6Renderer
                return PySide6Renderer(argv=self._argv, sfle_constraints=constraints)
            if binding == "pyside2":
                from psx.renderers.qt.pyside import PySide2Renderer
                return PySide2Renderer(argv=self._argv, sfle_constraints=constraints)
            if binding == "pyqt6":
                from psx.renderers.qt.pyqt import PyQt6Renderer
                return PyQt6Renderer(argv=self._argv, sfle_constraints=constraints)
            if binding == "pyqt5":
                from psx.renderers.qt.pyqt import PyQt5Renderer
                return PyQt5Renderer(argv=self._argv, sfle_constraints=constraints)
            if binding == "kivy":
                from kivy.core.window import Window
                Window.size = (width, height)
                from psx.renderers.kivy import KivyRenderer
                return KivyRenderer(sfle_constraints=constraints)
            if binding == "tkinter":
                from psx.renderers.tkinter import TkinterRenderer
                return TkinterRenderer(sfle_constraints=constraints)
        except ImportError as exc:
            raise FrameworkNotAvailableError(
                binding, f"Install the matching Velto extra: velto[{binding}]."
            ) from exc
        raise AssertionError("validated Velto binding did not select a renderer")

    def mount(self) -> Any:
        """Create the Velto app, mount the PSX root, and present its window."""
        if self._mounted:
            return self._handle
        settings = self.app_settings
        binding = self._binding(settings)
        width, height = self._window_size(settings)
        renderer = self._create_renderer(binding, width, height)
        try:
            from psx import App
        except ImportError as exc:  # pragma: no cover - packaging boundary
            raise FrameworkNotAvailableError("Velto", "Install qyro-engine with Velto available.") from exc

        app = App(self._root_component(), renderer=renderer)
        handle = app.mount()
        self._app, self._renderer, self._handle, self._mounted = app, renderer, handle, True
        self._present(binding, width, height)
        return handle

    def _present(self, binding: str, width: int, height: int) -> None:
        title = self.metadata.app_name
        icon = self.get_app_icon_path()
        if binding in {"pyside6", "pyside2", "pyqt6", "pyqt5"}:
            root_widget = self._handle.widget
            window = root_widget.window() if callable(getattr(root_widget, "window", None)) else root_widget
            window.resize(width, height)
            window.setWindowTitle(title)
            if icon:
                package = type(self._renderer.application).__module__.split(".")[0]
                gui = __import__(f"{package}.QtGui", fromlist=["QIcon"])
                qicon = gui.QIcon(icon)
                window.setWindowIcon(qicon)
                self._renderer.application.setWindowIcon(qicon)
            window.show()
        elif binding == "tkinter":
            root = self._renderer.root
            root.geometry(f"{width}x{height}")
            root.title(title)
            if icon:
                self._apply_tk_icon(root, icon)
        elif binding == "kivy":
            from kivy.core.window import Window
            Window.size = (width, height)
            Window.title = title
            if icon:
                Window.icon = icon

    @staticmethod
    def _apply_tk_icon(root: Any, icon: str) -> None:
        try:
            if icon.lower().endswith(".ico"):
                root.iconbitmap(icon)
            else:
                import tkinter as tk
                image = tk.PhotoImage(file=icon)
                root.iconphoto(True, image)
                root._qyro_icon_photo = image
        except Exception:
            pass

    def get_app_icon_path(self) -> str | None:
        raw = self.app_settings
        configured = raw.get("icon") or raw.get("app_icon")
        candidates = ([str(configured)] if configured else []) + [
            "icons/Icon.ico", "icons/512.png", "icons/256.png", "icons/128.png",
            "icons/64.png", "icons/32.png", "icons/app.png", "icons/icon.png",
            "icons/app.icns", "icons/icon.icns",
        ]
        for candidate in candidates:
            absolute = Path(candidate)
            if absolute.is_absolute() and absolute.exists():
                return str(absolute)
            parts = [part for part in candidate.replace("\\", "/").split("/") if part]
            try:
                resource = self.container.resolve_resource_use_case.execute(*parts, required=False)
                if resource.exists():
                    return str(resource)
            except Exception:
                continue
        return None

    def get_resource(self, *segments: str, required: bool = True) -> str:
        return str(self.container.resolve_resource_use_case.execute(*segments, required=required))

    def unmount(self) -> None:
        if self._app is not None and self._mounted:
            self._app.unmount()
        self._mounted = False
        self._handle = None

    def run(self) -> int:
        self.mount()
        return self._renderer.run()
