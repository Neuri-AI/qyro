"""Page widgets loaded by the application's tab layout."""

from .components import ComponentsView
from .container import ContainerView
from .context import ContextView
from .hello import HelloView
from .payloads import PayloadsView
from .pydux import PyduxView
from .resources import ResourcesView

__all__ = [
    "ComponentsView", "ContainerView", "ContextView", "HelloView",
    "PayloadsView", "PyduxView", "ResourcesView",
]
