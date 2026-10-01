"""
Resources Port Contract.
Locates and validates assets and resources regardless of environment.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from qyro.domain.entities import ResourceQuery, ResourceResult


class IResourcePort(ABC):
    """Abstract port for resolving assets and static files."""

    @abstractmethod
    def resolve(self, query: ResourceQuery) -> ResourceResult:
        """Resolves a resource query into an absolute verified file path."""
        pass

    @abstractmethod
    def list_resources(self, subdirectory: str = "") -> List[Path]:
        """Lists available resources in a given relative path."""
        pass
