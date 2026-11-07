"""Mobile platform detection should not depend on the packaging toolchain."""
import pytest

from qyro.adapters.platform.detector import PlatformDetector
from qyro.domain.entities import PlatformType


@pytest.mark.parametrize(
    ("platform", "expected"),
    [
        ("ios", PlatformType.IOS),
        ("iphoneos", PlatformType.IOS),
        ("android", PlatformType.ANDROID),
        ("darwin", PlatformType.MACOS),
        ("linux", PlatformType.LINUX),
        ("win32", PlatformType.WINDOWS),
    ],
)
def test_detect_mobile_and_desktop_platforms(monkeypatch, platform, expected):
    import qyro.adapters.platform.detector as detector
    monkeypatch.setattr(detector.sys, "platform", platform)
    monkeypatch.delattr(detector.sys, "getandroidapilevel", raising=False)
    assert PlatformDetector.get_platform() == expected


def test_android_python_reporting_linux(monkeypatch):
    import qyro.adapters.platform.detector as detector
    monkeypatch.setattr(detector.sys, "platform", "linux")
    monkeypatch.setattr(detector.sys, "getandroidapilevel", lambda: 35, raising=False)
    assert PlatformDetector.get_platform() == PlatformType.ANDROID
