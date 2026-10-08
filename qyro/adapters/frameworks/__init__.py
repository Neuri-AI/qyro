"""Framework adapters, loaded on demand to keep UI toolkits isolated."""

from importlib import import_module

from .base import BaseUIFrameworkAdapter
from .factory import FrameworkFactory

_LAZY_EXPORTS = {
    "BaseQtAdapter": (".qt_base", "BaseQtAdapter"),
    "PySide6Adapter": (".pyside6_adapter", "PySide6Adapter"),
    "PyQt6Adapter": (".pyqt6_adapter", "PyQt6Adapter"),
    "PySide2Adapter": (".pyside2_adapter", "PySide2Adapter"),
    "PyQt5Adapter": (".pyqt5_adapter", "PyQt5Adapter"),
    "KivyAdapter": (".kivy_adapter", "KivyAdapter"),
    "TkinterAdapter": (".tkinter_adapter", "TkinterAdapter"),
}


def __getattr__(name: str):
    """Preserve public adapter imports without initializing all frameworks."""
    try:
        module_name, class_name = _LAZY_EXPORTS[name]
    except KeyError as error:
        raise AttributeError(name) from error
    value = getattr(import_module(module_name, package=__name__), class_name)
    globals()[name] = value
    return value

__all__ = [
    "BaseUIFrameworkAdapter",
    "BaseQtAdapter",
    "PySide6Adapter",
    "PyQt6Adapter",
    "PySide2Adapter",
    "PyQt5Adapter",
    "KivyAdapter",
    "TkinterAdapter",
    "FrameworkFactory",
]
