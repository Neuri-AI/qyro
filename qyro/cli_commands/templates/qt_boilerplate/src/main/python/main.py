import sys
from qyro_engine.core.${binding} import AppEngine
from ${binding}.QtWidgets import QMainWindow, QLabel
from ${binding}.QtCore import Qt


class ${app_name}(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("${app_name}")
        self.setCentralWidget(QLabel("Hello, from Qyro!", alignment=Qt.AlignCenter))

if __name__ == '__main__':
    appctxt = AppEngine()
    app = ${app_name}()
    app.resize(800, 600)
    app.show()
    exec_func = getattr(appctxt.app, 'exec', appctxt.app.exec_)
    sys.exit(exec_func())