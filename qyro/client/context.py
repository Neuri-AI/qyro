"""
Qyro Application Context.
User-facing facade providing intuitive APIs while delegating to Clean Architecture use cases.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from qyro.container import EngineContainer
from qyro.domain.entities import AppMetadata, ExecutionMode, PlatformType


class ApplicationContext:
    """
    Primary user-facing context orchestrating application lifecycle,
    resource discovery and settings.
    Supports standalone instantiation and multiple-inheritance Mixin with QMainWindow.
    """

    _global_container: Optional[EngineContainer] = None
    _global_boot_info: Optional[Dict[str, Any]] = None

    @classmethod
    def _ensure_global_engine(
        cls,
        framework: Optional[str] = None,
        custom_root: Optional[Path] = None,
        enable_sentry: bool = True,
        argv: Optional[List[str]] = None,
    ) -> EngineContainer:
        """Ensures the global EngineContainer and UI application are initialized."""
        if cls._global_container is None:
            cls._global_container = EngineContainer(
                framework_name=framework,
                custom_root=custom_root,
                enable_sentry=enable_sentry,
            )
            cls._global_boot_info = cls._global_container.initialize_engine_use_case.execute(argv)
        return cls._global_container

    def _attach_engine_context(
        self,
        framework: Optional[str] = None,
        custom_root: Optional[Path] = None,
        enable_sentry: bool = True,
        argv: Optional[List[str]] = None,
    ) -> None:
        """
        Binds engine container, metadata, and application references to the instance.
        Safe to call multiple times; guarantees _metadata and _container exist.
        """
        ApplicationContext._ensure_global_engine(
            framework=framework,
            custom_root=custom_root,
            enable_sentry=enable_sentry,
            argv=argv,
        )
        container = ApplicationContext._global_container
        boot_info = ApplicationContext._global_boot_info or {}
        app_instance = boot_info.get("app_instance")

        # For Tkinter / single-window toolkits, bind self as app if not already established
        # Note: Check type(self) rather than self to avoid triggering SIP's super-class __init__ check on PyQt
        if not app_instance:
            try:
                if hasattr(type(self), "mainloop"):
                    app_instance = self
                    if container and hasattr(container.framework_adapter, "_app"):
                        container.framework_adapter._app = self
            except Exception:
                pass

        self._container = container
        self._boot_info = boot_info
        self._app = app_instance
        self._metadata = boot_info.get("metadata") or AppMetadata.default()

        # Safely assign without evaluating hasattr/getattr on uninitialized SIP objects
        try:
            has_title = hasattr(self, "_current_window_title")
        except (RuntimeError, AttributeError):
            has_title = False
        if not has_title:
            self._current_window_title = None

        try:
            has_icon = hasattr(self, "_current_icon_path")
        except (RuntimeError, AttributeError):
            has_icon = False
        if not has_icon:
            self._current_icon_path = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Wraps subclass __init__ so that when user subclasses (e.g. QMainWindow, ApplicationContext),
        the engine context, metadata, and QApplication are guaranteed to exist before and during __init__.
        """
        super().__init_subclass__(**kwargs)
        orig_init = cls.__init__

        if not getattr(orig_init, "_qyro_wrapped", False):
            def wrapped_init(self: Any, *args: Any, **kw: Any) -> None:
                # 1. Attach engine context attributes to self immediately
                # Ensures EngineContainer and QApplication exist BEFORE QMainWindow.__init__
                ApplicationContext._attach_engine_context(self)

                # 2. Call user's __init__ (which instantiates the C++ QMainWindow / widget)
                self._in_wrapped_init = True
                try:
                    orig_init(self, *args, **kw)
                finally:
                    self._in_wrapped_init = False

                # 3. Post-init auto configuration (title and icon)
                # Guaranteed safe now because orig_init has returned and C++ object is fully constructed
                if not getattr(self, "_auto_configured", False):
                    self._auto_configured = True

                    # Check if window already has an explicit custom title
                    already_has_title = False
                    if getattr(self, "_current_window_title", None):
                        already_has_title = True
                    elif hasattr(self, "windowTitle") and callable(getattr(self, "windowTitle")):
                        try:
                            t = self.windowTitle()
                            if t and str(t).strip():
                                already_has_title = True
                                self._current_window_title = str(t)
                        except Exception:
                            pass
                    elif hasattr(self, "title") and not callable(getattr(self, "title")) and getattr(self, "title"):
                        already_has_title = True
                        self._current_window_title = str(getattr(self, "title"))

                    default_title = self.get_default_window_title()
                    if not already_has_title:
                        try:
                            self.set_window_title(default_title, window=self)
                        except Exception:
                            pass

                    default_icon = self.get_app_icon_path()
                    if default_icon:
                        if self.container:
                            try:
                                self.container.framework_adapter.set_application_icon(default_icon)
                            except Exception:
                                pass
                        try:
                            self.set_window_icon(default_icon, window=self)
                        except Exception:
                            pass

            wrapped_init._qyro_wrapped = True
            cls.__init__ = wrapped_init

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        cls._ensure_global_engine(
            framework=kwargs.get("framework"),
            custom_root=kwargs.get("custom_root"),
            enable_sentry=kwargs.get("enable_sentry", True),
            argv=kwargs.get("argv"),
        )
        instance = super().__new__(cls)
        # Pre-bind engine attributes directly on instance during __new__
        boot_info = cls._global_boot_info or {}
        instance._container = cls._global_container
        instance._boot_info = boot_info
        instance._app = boot_info.get("app_instance")
        instance._metadata = boot_info.get("metadata") or AppMetadata.default()
        instance._current_window_title = None
        instance._current_icon_path = None
        return instance

    def __init__(
        self,
        framework: Optional[str] = None,
        custom_root: Optional[Path] = None,
        enable_sentry: bool = True,
        argv: Optional[List[str]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # CRITICAL: Always attach engine context attributes to self
        self._attach_engine_context(
            framework=framework,
            custom_root=custom_root,
            enable_sentry=enable_sentry,
            argv=argv,
        )

        self._current_window_title: Optional[str] = None
        self._current_icon_path: Optional[str] = None

        # Call cooperative next __init__ in MRO (e.g., QMainWindow(*args, **kwargs))
        try:
            super().__init__(*args, **kwargs)
        except TypeError:
            try:
                super().__init__()
            except Exception:
                pass

        # If this instance is being initialized within wrapped_init (e.g. subclass of QMainWindow),
        # DO NOT call set_window_title/set_window_icon here because the C++ base class
        # is still in the middle of its __init__ chain. wrapped_init will safely apply them once
        # the entire __init__ completes.
        if getattr(self, "_in_wrapped_init", False):
            return

        # Automatic Title & Icon Configuration from base.json and resources (for standalone usage)
        self._auto_configured = True
        default_title = self.get_default_window_title()
        default_icon = self.get_app_icon_path()

        if default_icon and self.container:
            try:
                self.container.framework_adapter.set_application_icon(default_icon)
            except Exception:
                pass

        # Auto-apply title and icon if self is a window instance (QMainWindow, tk.Tk, Kivy App)
        try:
            self.set_window_title(default_title, window=self)
        except Exception:
            pass

        if default_icon:
            try:
                self.set_window_icon(default_icon, window=self)
            except Exception:
                pass

    @property
    def container(self) -> EngineContainer:
        """Direct access to the underlying EngineContainer."""
        if not getattr(self, "_container", None):
            self._attach_engine_context()
        return self._container  # type: ignore

    @property
    def app(self) -> Any:
        """The native GUI application instance (e.g. QApplication or Kivy App)."""
        if not getattr(self, "_app", None):
            self._attach_engine_context()
        return getattr(self, "_app", None)

    @property
    def metadata(self) -> AppMetadata:
        """Application metadata object."""
        meta = getattr(self, "_metadata", None)
        if meta is None:
            self._attach_engine_context()
            meta = getattr(self, "_metadata", None)
        return meta or AppMetadata.default()

    @property
    def app_settings(self) -> Dict[str, Any]:
        """Alias for build settings dictionary (safe against framework method collisions)."""
        return self.metadata.raw_settings if self.metadata else {}

    @property
    def _safe_boot_info(self) -> Dict[str, Any]:
        if not getattr(self, "_boot_info", None):
            self._attach_engine_context()
        return getattr(self, "_boot_info", {}) or {}

    @property
    def is_frozen(self) -> bool:
        """True if running as a standalone compiled executable."""
        return self._safe_boot_info.get("is_frozen", False)

    @property
    def platform(self) -> PlatformType:
        """Host platform enum."""
        return self._safe_boot_info.get("platform", PlatformType.UNKNOWN)

    @property
    def execution_mode(self) -> ExecutionMode:
        """Detailed execution mode."""
        return self._safe_boot_info.get("execution_mode", ExecutionMode.SOURCE)

    # Window Title & Icon Management
    def get_default_window_title(self) -> str:
        """Returns the default window title defined in base.json or metadata."""
        meta_title = self.metadata.app_name if self.metadata else None
        raw_settings = self.metadata.raw_settings if self.metadata else {}
        settings_title = raw_settings.get("app_name") if isinstance(raw_settings, dict) else None
        return meta_title or settings_title or "Qyro Application"

    def get_window_title(self) -> str:
        """Returns the current window title."""
        if getattr(self, "_current_window_title", None):
            return self._current_window_title
        if hasattr(self, "windowTitle") and callable(getattr(self, "windowTitle")):
            try:
                t = self.windowTitle()
                if t and str(t).strip():
                    return str(t)
            except Exception:
                pass
        elif hasattr(self, "title") and not callable(getattr(self, "title")) and getattr(self, "title"):
            return str(getattr(self, "title"))
        return self.get_default_window_title()

    def set_window_title(self, title: str, window: Optional[Any] = None) -> bool:
        """
        Sets the window title on the target window (or self if used as a Mixin).
        Works transparently across Qt (setWindowTitle), Tkinter (title()), and Kivy (title).
        """
        target = window or self
        self._current_window_title = title
        applied = False

        if target and self.container:
            try:
                applied = self.container.framework_adapter.set_window_title(target, title)
            except (RuntimeError, Exception):
                pass

        if target and hasattr(target, "setWindowTitle"):
            try:
                target.setWindowTitle(title)
                applied = True
            except (RuntimeError, Exception):
                pass
        elif target and hasattr(target, "title") and callable(getattr(target, "title")):
            try:
                target.title(title)
                applied = True
            except (RuntimeError, Exception):
                pass
        elif target and hasattr(target, "title") and not callable(getattr(target, "title")):
            try:
                setattr(target, "title", title)
                applied = True
            except (RuntimeError, Exception):
                pass

        return applied

    @property
    def window_title(self) -> str:
        """Property for reading or setting the main window title."""
        return self.get_window_title()

    @window_title.setter
    def window_title(self, title: str) -> None:
        self.set_window_title(title)

    def get_app_icon_path(self) -> Optional[str]:
        """
        Discovers the primary application icon path using project settings (base.json)
        and platform-specific conventions (e.g. icons/app.ico, app.png, app.icns).
        """
        if getattr(self, "_current_icon_path", None):
            return self._current_icon_path

        # 1. Explicit setting in base.json ("icon": "icons/app.ico" or "app_icon": "...")
        raw_settings = self.metadata.raw_settings if self.metadata else {}
        explicit = (raw_settings.get("icon") or raw_settings.get("app_icon")) if isinstance(raw_settings, dict) else None
        if explicit and self.container:
            segments = [s for s in str(explicit).replace("\\", "/").split("/") if s]
            try:
                res = self.container.resolve_resource_use_case.execute(*segments, required=False)
                if res.exists():
                    self._current_icon_path = str(res)
                    return self._current_icon_path
            except Exception:
                pass

        # 2. Platform-aware candidate list
        candidates: List[str] = []
        if self.platform == PlatformType.WINDOWS:
            candidates.extend([
                "icons/Icon.ico",
                "icons/icon.ico",
                "icons/app.ico",
                "icons/64.png",
                "icons/32.png",
                "icons/24.png",
                "icons/16.png",
                "Icon.ico",
                "icon.ico",
                "app.ico"
            ])
        elif self.platform == PlatformType.MACOS:
            candidates.extend([
                "icons/512.png",
                "icons/256.png",
                "icons/128.png",
                "icons/1024.png",
                "icons/app.icns",
                "icons/icon.icns",
                "icons/Icon.ico",
                "icons/app.png"
            ])
        else:
            # Linux and BSD
            candidates.extend([
                "icons/512.png",
                "icons/256.png",
                "icons/128.png",
                "icons/1024.png",
                "icons/64.png",
                "icons/32.png",
                "icons/Icon.ico",
                "icons/app.png",
                "icons/icon.png"
            ])

        # Fallback search pool across all platforms
        candidates.extend([
            "icons/Icon.ico",
            "icons/512.png",
            "icons/256.png",
            "icons/128.png",
            "icons/64.png",
            "icons/32.png",
            "icons/24.png",
            "icons/16.png",
            "icons/icon.ico",
            "icons/app.ico",
            "icons/app.png",
            "icons/icon.png",
            "icons/app.icns",
            "icons/icon.icns",
            "Icon.ico",
            "icon.ico",
            "app.ico",
            "app.png",
        ])

        seen = set()
        for cand in candidates:
            if cand in seen:
                continue
            seen.add(cand)
            segments = cand.split("/")
            try:
                if self._container:
                    res = self._container.resolve_resource_use_case.execute(*segments, required=False)
                    if res.exists():
                        self._current_icon_path = str(res)
                        return self._current_icon_path
            except Exception:
                continue

        return None

    def set_window_icon(self, icon_path_or_relative: str, window: Optional[Any] = None) -> bool:
        """
        Sets the window icon on the target window and/or application singleton.
        Accepts absolute paths or relative resource paths (e.g. 'icons/app.ico').
        """
        target = window or self
        resolved_path = None

        if Path(icon_path_or_relative).exists():
            resolved_path = str(Path(icon_path_or_relative).resolve())
        elif self.container:
            segments = [s for s in str(icon_path_or_relative).replace("\\", "/").split("/") if s]
            try:
                res = self.container.resolve_resource_use_case.execute(*segments, required=False)
                if res.exists():
                    resolved_path = str(res)
            except Exception:
                pass

        if not resolved_path:
            return False

        self._current_icon_path = resolved_path
        applied = False

        if self.container:
            try:
                self.container.framework_adapter.set_application_icon(resolved_path)
            except (RuntimeError, Exception):
                pass
            if target:
                try:
                    applied = self.container.framework_adapter.set_window_icon(target, resolved_path)
                except (RuntimeError, Exception):
                    pass

        return applied or True

    @property
    def app_icon(self) -> Optional[str]:
        """Property for reading or setting the main application icon path."""
        return self.get_app_icon_path()

    @app_icon.setter
    def app_icon(self, icon_path: str) -> None:
        self.set_window_icon(icon_path)

    def get_resource(self, *segments: str, required: bool = True) -> str:
        """
        Resolves asset path segments and returns an absolute string path.
        Safe for use directly in Qt QIcon, QPixmap, stylesheets, etc.
        """
        path = self.container.resolve_resource_use_case.execute(*segments, required=required)
        return str(path)

    def run(self) -> int:
        """
        Default run implementation that starts the framework event loop.
        Can be overridden by user subclasses.
        """
        return self.container.framework_adapter.run()

    def exec(self) -> int:
        """Runs the framework application loop (Qt exec(), Tkinter mainloop(), or Kivy/adapter run())."""
        if hasattr(self, "mainloop") and callable(getattr(self, "mainloop")):
            getattr(self, "mainloop")()
            return 0
        if self._app and hasattr(self._app, "exec"):
            return self._app.exec()
        elif self._app and hasattr(self._app, "exec_"):
            return self._app.exec_()
        elif self._app and hasattr(self._app, "mainloop"):
            self._app.mainloop()
            return 0
        return self.run()

    def exec_(self) -> int:
        """Qt backward-compatibility alias for exec()."""
        return self.exec()


def app_is_frozen() -> bool:
    """Check if the current application is running inside a frozen executable."""
    if ApplicationContext._global_container:
        return ApplicationContext._global_container.env_adapter.is_frozen()
    container = EngineContainer()
    return container.env_adapter.is_frozen()


# Alias for convenience
is_frozen = app_is_frozen

