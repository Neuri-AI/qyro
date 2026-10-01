"""
Base UI Framework Adapter.
Common abstract implementation for GUI toolkits.
"""

from abc import abstractmethod
from typing import Any, List, Optional
from qyro.application.ports.ui_framework import IUIFrameworkPort


class BaseUIFrameworkAdapter(IUIFrameworkPort):
    """Base framework adapter storing app reference and lifecycle state."""

    def __init__(self) -> None:
        self._app: Any = None
        self._is_running: bool = False

    @property
    def app_instance(self) -> Any:
        return self._app