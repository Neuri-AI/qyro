from __future__ import annotations

from pathlib import Path

from qyro.adapters.resources.filesystem_resources import FileSystemResourceAdapter
from qyro.domain.entities import PlatformType, ResourceQuery


class _FakeEnv:
    def __init__(self, *, root: Path, bundle: Path, frozen: bool, platform: PlatformType) -> None:
        self._root = root
        self._bundle = bundle
        self._frozen = frozen
        self._platform = platform

    def is_frozen(self) -> bool:
        return self._frozen

    def get_root_dir(self) -> Path:
        return self._root

    def get_bundle_dir(self) -> Path:
        return self._bundle

    def get_platform(self) -> PlatformType:
        return self._platform


def test_resolve_accepts_base_prefixed_query_in_flat_frozen_resources(tmp_path: Path) -> None:
    bundle = tmp_path / "_internal"
    target = bundle / "resources" / "images" / "avatar.png"
    target.parent.mkdir(parents=True)
    target.write_text("png", encoding="utf-8")

    env = _FakeEnv(root=tmp_path, bundle=bundle, frozen=True, platform=PlatformType.WINDOWS)
    adapter = FileSystemResourceAdapter(env)

    result = adapter.resolve(ResourceQuery.from_segments("base", "images", "avatar.png"))

    assert result.exists is True
    assert result.absolute_path == target.resolve()


def test_resolve_accepts_platform_prefixed_query_in_flat_frozen_resources(tmp_path: Path) -> None:
    bundle = tmp_path / "_internal"
    target = bundle / "resources" / "icons" / "app.ico"
    target.parent.mkdir(parents=True)
    target.write_text("ico", encoding="utf-8")

    env = _FakeEnv(root=tmp_path, bundle=bundle, frozen=True, platform=PlatformType.WINDOWS)
    adapter = FileSystemResourceAdapter(env)

    result = adapter.resolve(ResourceQuery.from_segments("windows", "icons", "app.ico"))

    assert result.exists is True
    assert result.absolute_path == target.resolve()


def test_resolve_keeps_working_for_structured_base_resources(tmp_path: Path) -> None:
    bundle = tmp_path / "_internal"
    target = bundle / "resources" / "base" / "images" / "avatar.png"
    target.parent.mkdir(parents=True)
    target.write_text("png", encoding="utf-8")

    env = _FakeEnv(root=tmp_path, bundle=bundle, frozen=True, platform=PlatformType.WINDOWS)
    adapter = FileSystemResourceAdapter(env)

    result = adapter.resolve(ResourceQuery.from_segments("base", "images", "avatar.png"))

    assert result.exists is True
    assert result.absolute_path == target.resolve()
