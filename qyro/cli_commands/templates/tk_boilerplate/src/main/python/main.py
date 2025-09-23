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
        frm = ttk.Frame(self, padding=20)
        frm.grid()

        ttk.Label(frm, text="¡Hello World!").grid(column=0, row=0)
        ttk.Button(frm, text="Salir", command=self.destroy).grid(column=1, row=0)

if __name__ == "__main__":
    app = ${app_name}()
    app.mainloop()
    sys.exit(0)

