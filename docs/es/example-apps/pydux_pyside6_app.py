"""Reactive requiere invocar su limpieza; Component no hace unmount automático."""
from pathlib import Path
import sys

from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
from qyro import ApplicationContext, Component
from pydux import configure_store, create_slice
from pydux.adapters.qyro import Reactive


def create_store():
    counter = create_slice(
        "counter", {"value": 0},
        {"increment": lambda state, action: state.update(value=state["value"] + 1)},
    )
    return configure_store({"counter": counter}, devtools=False), counter


def create_ui():
    root_dir = None if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    context = ApplicationContext(framework="pyside6", custom_root=root_dir, enable_sentry=False)
    store, counter = create_store()

    class CounterWindow(QMainWindow, Component, Reactive):
        def render(self):
            self._closing = False
            central = QWidget(self)
            layout = QVBoxLayout(central)
            self.label = QLabel("Preparando contador", central)
            self.button = QPushButton("Incrementar", central)
            self.button.clicked.connect(lambda: store.dispatch(counter.actions.increment()))
            layout.addWidget(self.label)
            layout.addWidget(self.button)
            self.setCentralWidget(central)

        def component_did_mount(self):
            self.bind_selector(
                store, lambda state: state["counter"]["value"],
                self.update_label,
            )

        def update_label(self, value):
            if not self._closing:
                self.label.setText(f"Contador: {value}")

        def stop_bindings(self):
            self._closing = True
            self.component_will_unmount()

        def closeEvent(self, event):
            self.stop_bindings()
            super().closeEvent(event)

        def destroy_component(self):
            self.stop_bindings()
            super().destroy_component()

    window = CounterWindow()
    window.resize(420, 240)
    context.set_window_title("Qyro + Pydux opcional", window=window)
    context.app.aboutToQuit.connect(window.stop_bindings)
    return context, window, store, counter


def main():
    context, window, store, counter = create_ui()
    window.show()
    try:
        return context.run()
    finally:
        window.stop_bindings()


if __name__ == "__main__":
    raise SystemExit(main())
