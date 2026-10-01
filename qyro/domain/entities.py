"""
Domain Entities and Value Objects for Qyro.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class PlatformType(str, Enum):
    """Supported host operating system platforms."""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    ANDROID = "android"
    IOS = "ios"
    UNKNOWN = "unknown"

    @property
    def is_desktop(self) -> bool:
        return self in (PlatformType.WINDOWS, PlatformType.MACOS, PlatformType.LINUX)

    @property
    def is_mobile(self) -> bool:
        return self in (PlatformType.ANDROID, PlatformType.IOS)


class ExecutionMode(str, Enum):
    """Runtime execution environment detection."""
    SOURCE = "source"                      # Running from raw .py scripts
    FROZEN_PYINSTALLER = "pyinstaller"     # Standalone frozen executable
    FROZEN_GENERIC = "frozen_generic"      # Other bundlers (cx_Freeze, Briefcase)
    EMBEDDED = "embedded"


@dataclass(frozen=True)
class ResourceQuery:
    """Value object representing a resource lookup query."""
    relative_path_segments: Tuple[str, ...]

    def as_posix(self) -> str:
        return "/".join(self.relative_path_segments)

    @classmethod
    def from_segments(cls, *segments: str) -> "ResourceQuery":
        clean_segments = []
        for s in segments:
            parts = Path(s).parts
            clean_segments.extend(parts)
        return cls(relative_path_segments=tuple(clean_segments))


@dataclass(frozen=True)
class ResourceResult:
    """Resolved resource output with absolute path and metadata."""
    absolute_path: Path
    exists: bool
    is_bundled: bool
    target_os: Optional[PlatformType] = None


@dataclass
class AppMetadata:
    """Core application metadata loaded from build settings or runtime defaults."""
    app_name: str
    version: str = "0.1.0"
    author: str = ""
    identifier: str = ""
    description: str = ""
    raw_settings: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw_settings.get(key, default)

    @classmethod
    def default(cls) -> "AppMetadata":
        return cls(
            app_name="QyroApp",
            version="1.0.0",
            author="Author",
            identifier="com.qyro.app",
        )
