from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen

class TargeterApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        
        screen = MDScreen()
        label = MDLabel(text="Hello world!", halign="center")
        screen.add_widget(label)
        
        return screen

def main():
    TargeterApp().run()

if __name__ == "__main__":
    main()