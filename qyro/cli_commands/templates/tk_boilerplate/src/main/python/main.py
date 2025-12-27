import sys
import tkinter as tk
from qyro_engine.core.tkinter import AppEngine

class ${app_name}:
    def __init__(self, root):
        self.root = root
        self.render_()

    def render_(self):
        label = tk.Label(self.root, text="Hello, from Tkinter with Qyro!")
        label.pack(expand=True)

if __name__ == "__main__":
    appctxt = AppEngine()

    root = appctxt.app
    root.minsize(640, 480)

    app = ${app_name}(root)
    exec_func = root.exec_
    sys.exit(exec_func())
