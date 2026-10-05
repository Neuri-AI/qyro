"""Aplicación Qt: Component, settings, recursos, estilos y señales."""
from pathlib import Path
import sys

from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
from qyro import ApplicationContext, Component


class Panel(QWidget, Component):
    STYLES = "styles/panel.qss"

    def render(self):
        layout = QVBoxLayout(self)
        self.label = QLabel(self.props["details"], self)
        self.label.setWordWrap(True)
        self.counter = QLabel("0", self)
        self.count = 0
        self.button = QPushButton("Incrementar", self)
        self.button.clicked.connect(self.increment)
        layout.addWidget(self.label)
        layout.addWidget(self.counter)
        layout.addWidget(self.button)

    def increment(self):
        self.count += 1
        self.counter.setText(str(self.count))


def create_ui():
    root_dir = None if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    context = ApplicationContext(
        framework="pyside6", custom_root=root_dir, enable_sentry=False
    )
    window = QMainWindow()
    context.set_window_title(context.get_default_window_title(), window=window)
    size = context.app_settings.get("window", {})
    window.resize(size.get("width", 620), size.get("height", 360))
    welcome = Path(context.get_resource("texts", "welcome.txt")).read_text(encoding="utf-8")
    details = (
        f"{context.metadata.app_name} {context.metadata.version}\n"
        f"{context.platform.value} / {context.execution_mode.value}\n{welcome}"
    )
    panel = Panel(parent=window, details=details)
    window.setCentralWidget(panel)
    return context, window, panel


def main():
    context, window, panel = create_ui()
    window.show()
    return context.run()


if __name__ == "__main__":
    raise SystemExit(main())
