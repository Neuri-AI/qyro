
"""
Filesystem resource adapter implementing IResourcePort.

Resolves application resources across source and frozen environments,
including optional protected resource bundles.
"""

from pathlib import Path

from qyro.application.ports.environment import IEnvironmentPort
from qyro.application.ports.resources import IResourcePort
from qyro.adapters.resources.protected_bundle import ProtectedResourceBundle
from qyro.domain.entities import PlatformType, ResourceQuery, ResourceResult


class FileSystemResourceAdapter(IResourcePort):
    """Resolve resources across source and frozen directory hierarchies."""

    _PLATFORM_DIRECTORIES = {
        PlatformType.WINDOWS: ("windows", "win32"),
        PlatformType.MACOS: ("mac", "darwin"),
        PlatformType.LINUX: ("linux",),
    }

    _RESOURCE_ALIASES = frozenset({
        "base",
        "windows",
        "win32",
        "mac",
        "darwin",
        "linux",
    })

    def __init__(
        self,
        env_port: IEnvironmentPort,
        custom_resources_dir: Path | None = None,
    ) -> None:
        """Initialize the adapter with its environment and optional resource root."""
        self._env = env_port
        self._custom_resources_dir = custom_resources_dir

    def _get_candidate_roots(self) -> list[Path]:
        """Return resource directories in resolution priority order."""
        if self._custom_resources_dir is not None:
            custom_root = Path(self._custom_resources_dir).resolve()
            if custom_root.is_dir():
                return [custom_root]

        platform_dirs = self._PLATFORM_DIRECTORIES.get(
            self._env.get_platform(),
            (),
        )

        candidates: list[Path] = []

        if self._env.is_frozen():
            protected_root = ProtectedResourceBundle.get_extracted_root(
                self._env
            )

            if protected_root is not None:
                protected_resources = protected_root / "resources"
                candidates.extend(
                    self._resource_directories(
                        protected_resources,
                        platform_dirs,
                    )
                )

            bundle = self._env.get_bundle_dir()

            candidates.extend(
                self._resource_directories(
                    bundle / "resources",
                    platform_dirs,
                )
            )
            candidates.extend(
                self._resource_directories(
                    bundle / "src" / "main" / "resources",
                    platform_dirs,
                )
            )
            candidates.append(bundle)

        else:
            root = self._env.get_root_dir()

            candidates.extend(
                self._resource_directories(
                    root / "resources",
                    platform_dirs,
                )
            )
            candidates.extend(
                self._resource_directories(
                    root / "src" / "main" / "resources",
                    platform_dirs,
                )
            )

        return self._existing_unique_directories(candidates)

    @staticmethod
    def _resource_directories(
        root: Path,
        platform_dirs: tuple[str, ...],
    ) -> list[Path]:
        """Build platform-specific and shared resource directories."""
        return [
            *(root / directory for directory in platform_dirs),
            root / "base",
            root,
        ]

    @staticmethod
    def _existing_unique_directories(
        candidates: list[Path],
    ) -> list[Path]:
        """Filter missing directories and duplicates while preserving order."""
        unique: list[Path] = []
        seen: set[Path] = set()

        for candidate in candidates:
            path = candidate.resolve()

            if not path.is_dir() or path in seen:
                continue

            seen.add(path)
            unique.append(path)

        return unique

    def resolve(self, query: ResourceQuery) -> ResourceResult:
        """Resolve a resource query to an absolute filesystem path."""
        rel_path = Path(*query.relative_path_segments)
        rel_candidates = self._candidate_relative_paths(rel_path)
        candidates = self._get_candidate_roots()

        frozen = self._env.is_frozen()
        platform = self._env.get_platform()

        for root in candidates:
            for relative_path in rel_candidates:
                target = root / relative_path

                if target.is_file():
                    return ResourceResult(
                        absolute_path=target.resolve(),
                        exists=True,
                        is_bundled=frozen,
                        target_os=platform,
                    )

        primary_root = (
            candidates[0]
            if candidates
            else self._env.get_root_dir()
        )

        return ResourceResult(
            absolute_path=(primary_root / rel_path).resolve(),
            exists=False,
            is_bundled=frozen,
        )

    def _candidate_relative_paths(
        self,
        rel_path: Path,
    ) -> list[Path]:
        """Generate relative path variants for resource directory aliases."""
        alternatives = [rel_path]
        parts = rel_path.parts

        if (
            len(parts) >= 2
            and parts[0].lower() in self._RESOURCE_ALIASES
        ):
            alternatives.append(Path(*parts[1:]))

        return list(dict.fromkeys(alternatives))

    def list_resources(
        self,
        subdirectory: str = "",
    ) -> list[Path]:
        """List resources while preserving directory resolution priority."""
        relative_path = Path(subdirectory)
        results: list[Path] = []
        seen: set[Path] = set()

        for root in self._get_candidate_roots():
            target_dir = root / relative_path

            if not target_dir.is_dir():
                continue

            for path in target_dir.iterdir():
                resolved = path.resolve()

                if resolved in seen:
                    continue

                seen.add(resolved)
                results.append(resolved)

        return results
