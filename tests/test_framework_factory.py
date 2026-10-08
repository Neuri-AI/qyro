"""Regression tests for optional UI framework loading."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def test_explicit_tkinter_backend_does_not_import_qt() -> None:
    """Tk applications must not initialize an optional Qt binding first."""
    package_root = str(Path(__file__).resolve().parents[1])
    env = dict(os.environ)
    env["PYTHONPATH"] = package_root + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from qyro.adapters.frameworks.factory import FrameworkFactory; "
                "adapter = FrameworkFactory.create('tkinter'); "
                "assert adapter.framework_name == 'Tkinter'; "
                "assert not any(name.startswith(('PySide', 'PyQt')) for name in sys.modules)"
            ),
        ],
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
