"""Aplicación completa: contexto, settings, recurso y cierre nativo."""
from pathlib import Path
import sys
import tkinter as tk

from qyro import ApplicationContext


def create_ui():
    root_dir = None if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    context = ApplicationContext(
        framework="tkinter", custom_root=root_dir, enable_sentry=False
    )
    root = tk.Tk()
    context.set_window_title(context.get_default_window_title(), window=root)
    size = context.app_settings.get("window", {})
    root.geometry(f"{size.get('width', 620)}x{size.get('height', 360)}")
    welcome = Path(context.get_resource("texts", "welcome.txt")).read_text(encoding="utf-8")
    details = (
        f"{context.metadata.app_name} {context.metadata.version}\n"
        f"{context.platform.value} / {context.execution_mode.value}\n"
        f"{context.app_settings.get('platform_message', 'Configuración base')}\n\n"
        f"{welcome}"
    )
    tk.Label(root, text=details, wraplength=560, justify="left").pack(padx=24, pady=24)
    clicks = tk.IntVar(root, value=0)
    tk.Label(root, textvariable=clicks).pack()
    tk.Button(root, text="Incrementar", command=lambda: clicks.set(clicks.get() + 1)).pack()
    tk.Button(root, text="Cerrar", command=root.destroy).pack(pady=12)
    return context, root, clicks


def main():
    context, root, clicks = create_ui()
    return context.run()


if __name__ == "__main__":
    raise SystemExit(main())
