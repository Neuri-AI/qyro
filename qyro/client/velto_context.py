"""Velto-powered application context for Qyro.

Qyro owns configuration, resources and telemetry.  Velto owns the UI tree,
native renderer and event loop.
"""

from __future__ import annotations

from collections import deque

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
    stylesheets: ClassVar[tuple[str, ...]] = ()

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
        self._development_receiver = None
        self._development_changes = deque(maxlen=128)
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
        settings = self.metadata.raw_settings
        # A supervised development rollback can retain the last functional
        # backend without modifying the developer's configuration files.
        import os
        recovery = os.environ.get("VELTO_RECOVERY_FRAMEWORK")
        if (recovery and not self.is_frozen
                and os.environ.get("VELTO_DEVELOPMENT") == "1"):
            return {**settings, "framework": recovery, "binding": recovery}
        return settings

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
        compiled = [compiled_render]
        self._development_render = compiled

        def root() -> Any:
            # Keep source binding active whenever the component re-evaluates.
            from psx.css.context import scoped_css_resources

            configured = self.app_settings.get("css", {})
            if configured is None:
                configured = {}
            if not isinstance(configured, Mapping):
                raise TypeError("css settings must be an object.")
            settings_sheets = configured.get("stylesheets", ())
            class_sheets = getattr(self, "stylesheets", ())
            for sheets in (settings_sheets, class_sheets):
                if not isinstance(sheets, (list, tuple)) or not all(
                    isinstance(item, str) for item in sheets
                ):
                    raise TypeError("CSS stylesheets must be resource path sequences.")

            def read_resource(path: str) -> bytes:
                # Release Qyro extracts ordinary protected assets before
                # public get_resource returns their filesystem path.
                return Path(self.get_resource(path)).read_bytes()

            with scoped_css_resources(
                (*settings_sheets, *class_sheets), resolver=read_resource,
            ):
                return compiled[0](self)

        root.__name__ = f"{type(self).__name__}Root"
        root.__qualname__ = root.__name__
        definition = component(root)
        self._development_root_definition = definition
        return definition

    def _pydux_store(self) -> object | None:
        """Return the sole Pydux-compatible store declared by the view module.

        The store provider is an application boundary, so it must wrap the
        PSX root before the root component evaluates hooks. Keeping discovery
        here lets a ``VeltoContext.render`` method use Pydux hooks directly
        without a provider or an otherwise artificial child component.
        """
        explicit = getattr(self, "pydux_store", None)
        if explicit is not None:
            if not _is_pydux_store(explicit):
                raise TypeError("pydux_store must be a Pydux-compatible store.")
            return explicit

        namespace = getattr(type(self).render, "__globals__", {})
        stores = {id(value): value for value in namespace.values() if _is_pydux_store(value)}
        if len(stores) <= 1:
            return next(iter(stores.values()), None)
        raise RuntimeError(
            "More than one Pydux store is declared in this module; "
            "set pydux_store on the VeltoContext subclass."
        )

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

        # ``component`` returns a ComponentType. Calling it creates the VNode
        # that a provider can safely receive as its single child.
        root = self._root_component()()
        store = self._pydux_store()
        if store is not None:
            from .development_state import restore_restart_state
            restore_restart_state(self, store)
            try:
                from pydux import StoreProvider
            except ImportError as exc:  # pragma: no cover - packaging boundary
                raise FrameworkNotAvailableError(
                    "Pydux", "Install Pydux with its PSX integration available."
                ) from exc
            root = StoreProvider(store, root)

        app = App(root, renderer=renderer)
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

    def _start_development_receiver(self) -> None:
        """Connect only source, enabled applications to their CLI supervisor."""
        import os
        if (self.is_frozen or os.environ.get("VELTO_DEVELOPMENT") != "1"
                or os.environ.get("PSX_HOT_RELOAD") == "0"):
            return
        settings = self.app_settings.get("hot_reload", {})
        if not isinstance(settings, dict) or settings.get("enabled") is not True:
            return
        from .development_changes import DevelopmentChangeReceiver

        receiver = DevelopmentChangeReceiver(
            self._on_development_change,
            on_prepare_restart=self._on_development_restart_prepare,
        )
        receiver.start()
        self._development_receiver = receiver

    def _on_development_change(self, paths: tuple[str, ...]) -> None:
        """Dispatch refresh to the GUI owner thread, never the IPC thread."""
        if not self._mounted or self._renderer is None:
            return
        renderer = self._renderer
        renderer.schedule_ui(lambda: self._apply_development_change(paths))

    def _on_development_restart_prepare(self) -> None:
        """Prepare a development snapshot on the native UI owner thread."""
        if not self._mounted or self._renderer is None:
            return
        self._renderer.schedule_ui(self._prepare_development_restart)

    def _prepare_development_restart(self) -> None:
        from .development_state import capture_restart_state
        capture_restart_state(self)
        receiver = self._development_receiver
        if receiver is not None:
            receiver.acknowledge_restart()

    def _apply_development_change(self, paths: tuple[str, ...]) -> None:
        """Prepare compatible source edits and reevaluate the mounted root."""
        if not self._mounted or self._app is None:
            return
        import os
        from psx.devtools.coordinated_refresh import refresh_context_source
        source = os.environ.get("PSX_SOURCE_ENTRY")
        if not source:
            return
        # A changed native module already mapped into this interpreter cannot
        # safely be reloaded. A first import is not an unsafe replacement.
        from importlib.machinery import EXTENSION_SUFFIXES
        import sys
        root = Path(os.environ.get("VELTO_PROJECT_ROOT", Path(source).parent)).resolve()
        changed = set()
        for relative in paths:
            candidate = (root / relative).resolve()
            if candidate.is_relative_to(root):
                changed.add(candidate)
        native_changes = {path for path in changed if any(
            path.name.endswith(suffix) for suffix in EXTENSION_SUFFIXES
        )}
        if native_changes:
            loaded_native = {
                Path(filename).resolve()
                for module in tuple(sys.modules.values())
                if isinstance((filename := getattr(module, "__file__", None)), str)
                and any(filename.endswith(suffix) for suffix in EXTENSION_SUFFIXES)
            }
            if native_changes & loaded_native:
                receiver = self._development_receiver
                if receiver is not None:
                    from .development_state import capture_restart_state
                    capture_restart_state(self)
                    receiver.request_restart("loaded_native_extension_changed")
                return
        # Snapshot only explicitly opted-in, JSON-compatible Pydux state.
        store = None
        snapshot = None
        settings = self.app_settings.get("hot_reload", {})
        if isinstance(settings, dict) and settings.get("preserve_state") is True:
            try:
                from pydux.devtools.state_snapshot import capture_store_state
                store = self._pydux_store()
                if store is not None:
                    snapshot = capture_store_state(store)
            except (ImportError, TypeError, ValueError):
                store = None
                snapshot = None
        try:
            refresh_context_source(self, Path(source), paths)
        except Exception as exc:
            # Cleanup may fail after a replacement has already committed.
            reconciler = getattr(self._app, "reconciler", None)
            committed = bool(getattr(reconciler, "_coordinated_remount_applied", False))
            if store is not None and snapshot is not None and not committed:
                try:
                    from pydux.devtools.state_snapshot import restore_store_state
                    restore_store_state(store, snapshot)
                except Exception:
                    import logging
                    logging.getLogger("qyro.development").exception(
                        "Development store recovery failed"
                    )
            import logging
            logging.getLogger("qyro.development").warning("Source refresh rejected: %s", exc)

    def unmount(self) -> None:
        if self._development_receiver is not None:
            self._development_receiver.stop()
            self._development_receiver = None
        if self._app is not None and self._mounted:
            self._app.unmount()
        self._mounted = False
        self._handle = None

    def run(self) -> int:
        self.mount()
        self._start_development_receiver()
        try:
            return self._renderer.run()
        finally:
            if self._development_receiver is not None:
                self._development_receiver.stop()
                self._development_receiver = None


def _is_pydux_store(value: object) -> bool:
    """Recognize Pydux's public store protocol without a hard dependency."""
    return not isinstance(value, type) and all(
        callable(getattr(value, name, None)) for name in ("get_state", "dispatch", "select")
    )
