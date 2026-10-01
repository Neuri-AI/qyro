"""
Resolve Resource Use Case.
Encapsulates domain logic for locating application assets and files.
"""

from pathlib import Path
from qyro.application.ports.resources import IResourcePort
from qyro.domain.entities import ResourceQuery, ResourceResult
from qyro.domain.errors import ResourceNotFoundError


class ResolveResourceUseCase:
    """Use case to safely resolve assets with domain validation."""

    def __init__(self, resource_port: IResourcePort) -> None:
        self._port = resource_port

    def execute(self, *segments: str, required: bool = True) -> Path:
        """
        Resolves relative path segments to an absolute filesystem Path.
        If required=True and file does not exist, raises ResourceNotFoundError.
        """
        query = ResourceQuery.from_segments(*segments)
        result: ResourceResult = self._port.resolve(query)

        if required and not result.exists:
            searched = [str(result.absolute_path.parent)]
            raise ResourceNotFoundError(query.as_posix(), searched)

        return result.absolute_path
