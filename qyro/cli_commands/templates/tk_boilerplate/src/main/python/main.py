import sys
import tkinter as tk
from tkinter import ttk

class ${app_name}(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("${app_name}")
        self.geometry("300x100")
        self.render_()

    def render_(self):
        label = ttk.Label(self, text="Hello, from Qyro!")
        label.pack(expand=True, anchor="center")

if __name__ == "__main__":
    app = ${app_name}()
    app.mainloop()
    sys.exit(0)

