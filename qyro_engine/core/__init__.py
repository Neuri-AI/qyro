import importlib
import sys
import logging
from typing import Callable, TypeVar, Any, Union
from collections import namedtuple
from functools import lru_cache, wraps
from qyro.utils.platform import EngineError, windows_based, mac_based
from qyro_engine.utils import app_is_frozen
from qyro_engine._signal import QtSignalHandler
from qyro_engine._frozen import load_frozen_build_settings, get_frozen_resource_dirs
from qyro_engine._source import find_project_root_directory, get_project_resource_locations, load_build_configurations
from qyro_engine.utils.resources import FileLocator
from qyro_engine.exceptions.excepthooks import StderrExceptionHandler, _Excepthook


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_T = TypeVar('_T')
QtBinding = namedtuple(
    'QtBinding', ['QApplication', 'QIcon', 'QAbstractSocket'])
TkBinding = namedtuple('TkBinding', ['Tk', 'PhotoImage'])
KivyBinding = namedtuple('KivyBinding', ['App', 'Window', 'Config'])
available_bindings = {}


def lazy_property(func: Callable[[Any], _T]) -> _T:
    @wraps(func)
    @lru_cache(maxsize=1)
    def wrapper(self):
        return func(self)
    return property(wrapper)


def load_binding(binding_name: str) -> Union[QtBinding, TkBinding, KivyBinding]:
    """This ensures that the specified binding is loaded and available.

    Args:
        binding_name (str): The name of the binding to load (e.g., 'PyQt5', 'PySide6', 'Tkinter').

    Raises:
        ValueError: If the specified binding name is unknown.
        ImportError: If the required modules for the binding cannot be imported.

    Returns:
        Union[QtBinding, TkBinding]: The loaded binding object.
    """
    try:
        if binding_name == 'PyQt5' or binding_name == 'PyQt6' or binding_name == 'PySide2' or binding_name == 'PySide6':
            widgets = importlib.import_module(f'{binding_name}.QtWidgets')
            gui = importlib.import_module(f'{binding_name}.QtGui')
            network = importlib.import_module(f'{binding_name}.QtNetwork')
            return QtBinding(
                QApplication=getattr(widgets, 'QApplication'),
                QIcon=getattr(gui, 'QIcon'),
                QAbstractSocket=getattr(network, 'QAbstractSocket')
            )

        if binding_name == 'kivy':
            kivy_app = importlib.import_module('kivy.app')
            kivy_core_window = importlib.import_module('kivy.core.window')
            kivy_config = importlib.import_module('kivy.config')
            return KivyBinding(
                App=getattr(kivy_app, 'App'),
                Window=getattr(kivy_core_window, 'Window'),
                Config=getattr(kivy_config, 'Config')
            )

        if binding_name == 'tkinter':
            tk = importlib.import_module('tkinter')
            return TkBinding(
                Tk=getattr(tk, 'Tk'),
                PhotoImage=getattr(tk, 'PhotoImage')
            )
        raise ValueError(f"Unknown binding name: {binding_name}")
    except ModuleNotFoundError as e:
        raise ImportError(
            f"Cannot load Qt binding '{binding_name}'. Module not found: {e}")


class _AppEngine:
    """
    Base engine para apps Qt con bindings dinámicos.
    """
    preferred_binding = 'PySide6'
    _binding = None

    def __init__(self, argv: list[str] = None):
        self._argv = argv or sys.argv

        if not self._binding:
            self._binding = self.preferred_binding

        available_bindings[self._binding] = load_binding(self._binding)

        self.app = self.get_application_instance

        if not self.set_app_icon:
            return

        if self._binding == "tkinter":
            self._set_tkinter_icon()

        if self._binding not in ['kivy', 'tkinter']:
            self.app.setWindowIcon(self.set_app_icon)

        # Manejo de excepciones y señales
        self.exception_handler = StderrExceptionHandler()
        self.install_exception_hook()
        self.setup_signal_handler()

    def _set_tkinter_icon(self):
        binding = available_bindings[self._binding]
        try:
            self.app.iconphoto(True, binding.PhotoImage(
                file=self._resource('Icon.ico')))
        except EngineError as e:
            logger.warning(f"Failed to set Tkinter icon: {e}")

    @staticmethod
    def _validate_binding(binding_name: str, binding: QtBinding):
        if not isinstance(binding, QtBinding):
            raise TypeError(f"Invalid Qt binding type for '{binding_name}'")
        if binding.QApplication is None:
            raise ValueError(
                f"QApplication class not found for binding '{binding_name}'")

    @lazy_property
    def get_application_instance(self):
        binding = available_bindings[self._binding]
        build_settings = self.load_build_settings()

        if self._binding == "tkinter":
            app_instance = binding.Tk()
            app_instance.title(build_settings.get('app_name', 'Qyro App'))

            app_instance.exec_ = app_instance.mainloop
            return app_instance

        elif self._binding == "kivy":
            if not self._resource('Icon.png') or not self._resource('Icon.ico'):
                raise EngineError("Icon file not found for Kivy application.")

            icon_path = self._resource('Icon.png')
            if not icon_path:
                icon_path = self._resource('Icon.ico')

            class QyroKivyApp(binding.App):
                def build(self):
                    # Kivy Calls to build() when running the app
                    # We allow the user to inject their root widget into 'self.user_root'
                    # before calling exec_().
                    return getattr(self, 'user_root', None)

            app_instance = QyroKivyApp()
            app_instance.title = build_settings.get('app_name', 'Qyro App')
            app_instance.icon = icon_path

            # override exec_ to call run()
            app_instance.exec_ = app_instance.run
            return app_instance

        else:
            self._validate_binding(self._binding, binding)
            app = binding.QApplication(self._argv)
            app.setApplicationName(build_settings.get('app_name', 'Qyro App'))
            app.setOrganizationName(
                build_settings.get('organization_name', 'Qyro'))
            app.setApplicationVersion(build_settings.get('version', '1.0.0'))
            return app

    @lazy_property
    def get_resource_locator(self):
        if app_is_frozen():
            # For frozen applications
            resource_dirs = get_frozen_resource_dirs()
        else:
            # For runtime applications (not frozen)
            project_root = find_project_root_directory()
            resource_dirs = get_project_resource_locations(project_root)
        return FileLocator(resource_dirs)

    def _resource(self, path):
        return self.get_resource_locator.find(path)

    @lazy_property
    def set_app_icon(self):
        if mac_based():
            return None

        binding = available_bindings[self._binding]

        if self._binding in ['tkinter', 'kivy']:
            return self._resource('Icon.ico')

        return binding.QIcon(self._resource('Icon.ico'))

    def install_exception_hook(self):
        _Excepthook(self.exception_handler)

    def setup_signal_handler(self):

        if self._binding in ['tkinter', 'kivy']:
            return

        if not windows_based():
            binding = available_bindings[self._binding]
            QtSignalHandler(self.app, binding.QAbstractSocket).install()

    def load_build_settings(self) -> dict:
        if app_is_frozen():
            return load_frozen_build_settings()
        else:
            project_root = find_project_root_directory()
            return load_build_configurations(project_root)
