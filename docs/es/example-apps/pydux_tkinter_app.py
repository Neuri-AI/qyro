"""Pydux es una dependencia independiente; dispatch ocurre en el hilo UI."""
from pathlib import Path
import sys
import tkinter as tk

from qyro import ApplicationContext
from pydux import configure_store, create_slice
from pydux.adapters.base import ReactiveBinding
from pydux.adapters.tkinter import TkinterBridge


def create_ui():
    root_dir = None if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    context = ApplicationContext(framework="tkinter", custom_root=root_dir, enable_sentry=False)
    root = tk.Tk()
    context.set_window_title("Qyro + Pydux opcional", window=root)
    root.geometry("420x240")
    counter = create_slice(
        "counter", {"value": 0},
        {"increment": lambda state, action: state.update(value=state["value"] + 1)},
    )
    store = configure_store({"counter": counter}, devtools=False)
    label = tk.Label(root, text="Preparando contador")
    label.pack(pady=24)
    closing = False

    def update_label(value):
        if not closing:
            label.configure(text=f"Contador: {value}")

    binding = ReactiveBinding(
        store, lambda state: state["counter"]["value"],
        update_label,
        bridge=TkinterBridge(root),
    )
    button = tk.Button(root, text="Incrementar", command=lambda: store.dispatch(counter.actions.increment()))
    button.pack()

    def close():
        nonlocal closing
        closing = True
        binding.dispose()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    tk.Button(root, text="Cerrar", command=close).pack(pady=12)
    return context, root, store, counter, label, button, binding


def main():
    context, root, store, counter, label, button, binding = create_ui()
    try:
        return context.run()
    finally:
        binding.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
