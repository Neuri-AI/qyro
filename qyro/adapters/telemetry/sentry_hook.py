"""
Sentry Exception Hook Adapter.
Sends production crashes to Sentry when sentry-sdk is available and DSN is configured.
"""

import os
import sys
from types import TracebackType
from typing import Optional, Type
from qyro.application.ports.telemetry import ITelemetryPort


class SentryExceptionHookAdapter(ITelemetryPort):
    """Integrates sentry-sdk gracefully with zero hard crash if not installed."""

    def __init__(self, dsn: str = "", environment: str = "production", release: str = "") -> None:
        self._dsn = dsn or os.environ.get("SENTRY_DSN", "")
        self._environment = environment
        self._release = release
        self._sentry_available = False

    def install(self) -> None:
        if not self._dsn:
            return

        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=self._dsn,
                environment=self._environment,
                release=self._release,
                traces_sample_rate=0.2,
            )
            self._sentry_available = True
        except ImportError:
            print("[Qyro Warning] SENTRY_DSN configured but 'sentry-sdk' is not installed.")
        except Exception as e:
            print(f"[Qyro Warning] Failed to initialize Sentry: {e}")

    def handle_exception(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback: Optional[TracebackType],
    ) -> None:
        if self._sentry_available:
            try:
                import sentry_sdk
                sentry_sdk.capture_exception((exc_type, exc_value, exc_traceback))
            except Exception:
                pass
