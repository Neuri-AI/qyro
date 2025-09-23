import kivy
from kivy.app import App
from kivy.uix.label import Label

kivy.require('2.3.1')

class ${app_name}(App):
    def build(self):
        return Label(text="Hello, from Qyro!")

if __name__ == '__main__':
    ${app_name}().run()