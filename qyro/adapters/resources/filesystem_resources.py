"""
Filesystem resource adapter that implements IResourcePort by resolving
assets across source and frozen directory hierarchies.
"""

from pathlib import Path

from qyro.application.ports.environment import IEnvironmentPort
from qyro.application.ports.resources import IResourcePort
from qyro.domain.entities import PlatformType, ResourceQuery, ResourceResult


class FileSystemResourceAdapter(IResourcePort):
    """Resolves assets across multi-tiered directory structures."""

    def __init__(
        self,
        env_port: IEnvironmentPort,
        custom_resources_dir: Path | None = None,
    ) -> None:
        """Initialize the resource adapter with the environment and resource directory."""
        self._env = env_port
        self._custom_resources_dir = custom_resources_dir

    def _get_candidate_roots(self) -> list[Path]:
        """Return existing directories that may contain application resources."""
        if self._custom_resources_dir and self._custom_resources_dir.exists():
            return [self._custom_resources_dir]

        platform = self._env.get_platform()
        platform_subdir_map = {
            PlatformType.WINDOWS: ["windows", "win32"],
            PlatformType.MACOS: ["mac", "darwin"],
            PlatformType.LINUX: ["linux"],
        }
        os_dirs = platform_subdir_map.get(platform, [])

        candidates: list[Path] = []

        if self._env.is_frozen():
            bundle = self._env.get_bundle_dir()

            for os_sub in os_dirs:
                candidates.append(bundle / "resources" / os_sub)
                candidates.append(
                    bundle / "src" / "main" / "resources" / os_sub
                )

            candidates.extend(
                [
                    bundle / "resources" / "base",
                    bundle / "resources",
                    bundle / "src" / "main" / "resources" / "base",
                    bundle,
                ]
            )
        else:
            root = self._env.get_root_dir()

            for os_sub in os_dirs:
                candidates.append(root / "resources" / os_sub)
                candidates.append(
                    root / "src" / "main" / "resources" / os_sub
                )

            candidates.extend(
                [
                    root / "resources" / "base",
                    root / "resources",
                    root / "src" / "main" / "resources" / "base",
                    root / "src" / "main" / "resources",
                ]
            )

        unique: list[Path] = []
        for candidate in candidates:
            if candidate.exists() and candidate not in unique:
                unique.append(candidate)

        return unique

    def resolve(self, query: ResourceQuery) -> ResourceResult:
        """Resolve a resource query to its absolute filesystem path."""
        rel_path = Path(*query.relative_path_segments)
        candidates = self._get_candidate_roots()

        for root in candidates:
            target = root / rel_path
            if target.exists():
                return ResourceResult(
                    absolute_path=target.resolve(),
                    exists=True,
                    is_bundled=self._env.is_frozen(),
                    target_os=self._env.get_platform(),
                )

        primary_root = (
            candidates[0] if candidates else self._env.get_root_dir()
        )
        fallback_path = (primary_root / rel_path).resolve()

        return ResourceResult(
            absolute_path=fallback_path,
            exists=False,
            is_bundled=self._env.is_frozen(),
        )

    def list_resources(self, subdirectory: str = "") -> list[Path]:
        """List resources contained in the specified subdirectory."""
        rel = Path(subdirectory)
        results: list[Path] = []

        for root in self._get_candidate_roots():
            target_dir = root / rel
            if target_dir.exists() and target_dir.is_dir():
                results.extend(
                    path.resolve() for path in target_dir.iterdir()
                )

        return list(set(results))