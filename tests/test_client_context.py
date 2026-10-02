from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from qyro.client.context import ApplicationContext
from qyro.domain.entities import AppMetadata, ExecutionMode, PlatformType


class _FakeFrameworkAdapter:
    def __init__(self) -> None:
        self.run_code = 0
        self.window_title_calls: list[tuple[Any, str]] = []
        self.window_icon_calls: list[tuple[Any, str]] = []
        self.app_icon_calls: list[str] = []

    def run(self) -> int:
        return self.run_code

    def set_window_title(self, window: Any, title: str) -> bool:
        self.window_title_calls.append((window, title))
        return True

    def set_window_icon(self, window: Any, icon_path: str) -> bool:
        self.window_icon_calls.append((window, icon_path))
        return True

    def set_application_icon(self, icon_path: str) -> bool:
        self.app_icon_calls.append(icon_path)
        return True


class _FakeResolveResourceUseCase:
    def __init__(self, mapping: dict[str, Path]) -> None:
        self.mapping = mapping

    def execute(self, *segments: str, required: bool = True) -> Path:
        key = "/".join(segments)
        value = self.mapping.get(key)
        if value is None:
            value = Path("__missing__")
        if required and not value.exists():
            raise FileNotFoundError(key)
        return value


class _FakeContainer:
    def __init__(self, mapping: dict[str, Path] | None = None) -> None:
        self.framework_adapter = _FakeFrameworkAdapter()
        self.resolve_resource_use_case = _FakeResolveResourceUseCase(mapping or {})


@pytest.fixture(autouse=True)
def _reset_application_context_globals() -> None:
    ApplicationContext._global_container = None
    ApplicationContext._global_boot_info = None
    yield
    ApplicationContext._global_container = None
    ApplicationContext._global_boot_info = None


def _bind_fake_engine(
    monkeypatch: pytest.MonkeyPatch,
    *,
    container: _FakeContainer,
    metadata: AppMetadata | None = None,
    app_instance: Any = object(),
    is_frozen: bool = False,
    platform: PlatformType = PlatformType.UNKNOWN,
    execution_mode: ExecutionMode = ExecutionMode.SOURCE,
) -> None:
    boot_info = {
        "metadata": metadata or AppMetadata.default(),
        "app_instance": app_instance,
        "is_frozen": is_frozen,
        "platform": platform,
        "execution_mode": execution_mode,
    }

    def _fake_ensure(
        cls: type[ApplicationContext],
        framework: str | None = None,
        custom_root: Path | None = None,
        enable_sentry: bool = True,
        argv: list[str] | None = None,
    ) -> _FakeContainer:
        cls._global_container = container  # type: ignore[assignment]
        cls._global_boot_info = boot_info
        return container

    monkeypatch.setattr(ApplicationContext, "_ensure_global_engine", classmethod(_fake_ensure))


def test_run_delegates_to_framework_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    container = _FakeContainer()
    container.framework_adapter.run_code = 17
    _bind_fake_engine(monkeypatch, container=container)

    context = ApplicationContext()

    assert context.run() == 17


def test_default_properties_come_from_boot_info(monkeypatch: pytest.MonkeyPatch) -> None:
    container = _FakeContainer()
    metadata = AppMetadata(app_name="MyApp", raw_settings={"theme": "dark"})
    _bind_fake_engine(
        monkeypatch,
        container=container,
        metadata=metadata,
        is_frozen=True,
        platform=PlatformType.WINDOWS,
        execution_mode=ExecutionMode.FROZEN_PYINSTALLER,
    )

    context = ApplicationContext()

    assert context.metadata.app_name == "MyApp"
    assert context.app_settings["theme"] == "dark"
    assert context.is_frozen is True
    assert context.platform == PlatformType.WINDOWS
    assert context.execution_mode == ExecutionMode.FROZEN_PYINSTALLER


def test_get_default_window_title_uses_metadata_first(monkeypatch: pytest.MonkeyPatch) -> None:
    container = _FakeContainer()
    metadata = AppMetadata(app_name="MetaName", raw_settings={"app_name": "SettingsName"})
    _bind_fake_engine(monkeypatch, container=container, metadata=metadata)

    context = ApplicationContext()

    assert context.get_default_window_title() == "MetaName"


def test_set_window_title_applies_to_framework_and_target(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Window:
        def __init__(self) -> None:
            self.title = ""

        def setWindowTitle(self, title: str) -> None:
            self.title = title

    container = _FakeContainer()
    _bind_fake_engine(monkeypatch, container=container)
    context = ApplicationContext()
    window = _Window()

    applied = context.set_window_title("Hello", window=window)

    assert applied is True
    assert window.title == "Hello"
    assert container.framework_adapter.window_title_calls[-1][1] == "Hello"


def test_get_app_icon_path_uses_explicit_icon_setting(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    icon = tmp_path / "resources" / "icons" / "app.ico"
    icon.parent.mkdir(parents=True)
    icon.write_text("ico", encoding="utf-8")

    mapping = {"icons/app.ico": icon}
    container = _FakeContainer(mapping)
    metadata = AppMetadata(app_name="MyApp", raw_settings={"icon": "icons/app.ico"})
    _bind_fake_engine(monkeypatch, container=container, metadata=metadata)

    context = ApplicationContext()

    assert context.get_app_icon_path() == str(icon)


def test_get_app_icon_path_uses_platform_candidates(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    icon = tmp_path / "resources" / "icons" / "32.png"
    icon.parent.mkdir(parents=True)
    icon.write_text("png", encoding="utf-8")

    mapping = {"icons/32.png": icon}
    container = _FakeContainer(mapping)
    metadata = AppMetadata(app_name="MyApp", raw_settings={})
    _bind_fake_engine(monkeypatch, container=container, metadata=metadata, platform=PlatformType.WINDOWS)

    context = ApplicationContext()

    assert context.get_app_icon_path() == str(icon)


def test_set_window_icon_with_absolute_path_calls_adapter(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    icon = tmp_path / "abs-icon.ico"
    icon.write_text("ico", encoding="utf-8")

    class _Window:
        pass

    container = _FakeContainer()
    _bind_fake_engine(monkeypatch, container=container)
    context = ApplicationContext()
    window = _Window()

    applied = context.set_window_icon(str(icon), window=window)

    assert applied is True
    assert context.app_icon == str(icon.resolve())
    assert container.framework_adapter.app_icon_calls[-1] == str(icon.resolve())
    assert container.framework_adapter.window_icon_calls[-1][1] == str(icon.resolve())


def test_get_resource_returns_string_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "resources" / "images" / "logo.png"
    target.parent.mkdir(parents=True)
    target.write_text("png", encoding="utf-8")

    mapping = {"images/logo.png": target}
    container = _FakeContainer(mapping)
    _bind_fake_engine(monkeypatch, container=container)

    context = ApplicationContext()

    assert context.get_resource("images", "logo.png") == str(target)
