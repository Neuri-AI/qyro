"""
Domain Exceptions for Qyro.
Hierarchy of clean domain errors independent of specific GUI/OS technologies.
"""


class QyroEngineError(Exception):
    """Base exception for all Qyro runtime and domain errors."""
    def __init__(self, message: str, details: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class ResourceNotFoundError(QyroEngineError):
    """Raised when an asset or resource cannot be located in any resource scope."""
    def __init__(self, resource_name: str, search_paths: list[str]) -> None:
        searched_in = ", ".join(search_paths)
        super().__init__(
            f"Resource '{resource_name}' could not be resolved.",
            f"Searched in: [{searched_in}]"
        )
        self.resource_name = resource_name
        self.search_paths = search_paths


class SettingsNotFoundError(QyroEngineError):
    """Raised when required settings (base.json or OS override) are missing."""
    pass


class FrameworkNotAvailableError(QyroEngineError):
    """Raised when a requested UI framework (PySide6, PyQt6, Kivy, etc.) is not installed."""
    def __init__(self, framework_name: str, install_hint: str = "") -> None:
        msg = f"Requested UI framework '{framework_name}' is not installed or available in Python environment."
        if not install_hint:
            install_hint = f"Run 'pip install {framework_name.lower()}' or poetry add {framework_name.lower()}."
        super().__init__(msg, install_hint)
        self.framework_name = framework_name


class PlatformUnsupportedError(QyroEngineError):
    """Raised when an operation is executed on an unsupported host OS."""
    pass
