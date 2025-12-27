import sys
import kivy
from qyro_engine.core.kivy import AppEngine
from kivy.uix.label import Label

kivy.require('2.3.1')

class ${app_name}(AppEngine):
    def __init__(self):
        super().__init__()
        ui = Label(
            text='Hello, world from Qyro with Kivy!',
            font_size='24sp'
        )

        # Inject the root UI widget into the application lifecycle
        # This widget becomes the main entry point for rendering
        self.app.user_root = ui

if __name__ == '__main__':
    appctxt = ${app_name}()
    exec_func = appctxt.app.exec_
    sys.exit(exec_func())