"""Kivy construye su árbol una vez en build; Qyro aporta contexto y rutas."""
from pathlib import Path
import sys

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from qyro import ApplicationContext


class ExampleApp(App):
    def __init__(self, context, **kwargs):
        super().__init__(**kwargs)
        self.context = context
        self.title = context.get_default_window_title()
        self.count = 0

    def build(self):
        layout = BoxLayout(orientation="vertical", padding=24, spacing=12)
        welcome = Path(self.context.get_resource("texts", "welcome.txt")).read_text(encoding="utf-8")
        text = f"{self.title}\n{self.context.execution_mode.value}\n{welcome}"
        layout.add_widget(Label(text=text))
        self.counter = Label(text="0")
        button = Button(text="Incrementar")
        button.bind(on_release=self.increment)
        layout.add_widget(self.counter)
        layout.add_widget(button)
        return layout

    def increment(self, *args):
        self.count += 1
        self.counter.text = str(self.count)


def main():
    root_dir = None if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    context = ApplicationContext(framework="kivy", custom_root=root_dir, enable_sentry=False)
    ExampleApp(context).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
