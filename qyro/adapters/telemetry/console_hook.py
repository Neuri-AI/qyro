"""
Console and Standard Error Hook Adapter.
Logs uncaught exceptions and prevents silent crash of GUI event loops.
"""

import sys
import traceback
from types import TracebackType
from typing import Optional, Type
from qyro.application.ports.telemetry import ITelemetryPort


class ConsoleExceptionHookAdapter(ITelemetryPort):
    """Prints unhandled exceptions cleanly and logs system diagnostics."""

    def __init__(self, show_banner: bool = True) -> None:
        self._show_banner = show_banner
        self._original_hook = sys.excepthook

    def install(self) -> None:
        sys.excepthook = self.handle_exception

    def handle_exception(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback: Optional[TracebackType],
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow clean Ctrl+C termination
            self._original_hook(exc_type, exc_value, exc_traceback)
            return

        print("\n" + "=" * 65, file=sys.stderr)
        print("  [Qyro] Unhandled Exception Caught in Event Loop", file=sys.stderr)
        print("=" * 65, file=sys.stderr)
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        print("=" * 65 + "\n", file=sys.stderr)