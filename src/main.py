# Kivy
from kivymd.app import MDApp
from kivy.logger import Logger as log, LOG_LEVELS
from kivy.config import Config
from kivy.uix.screenmanager import ScreenManager
from kivy.resources import resource_add_path
from kivy.animation import Animation
from kivy.metrics import dp
# KivyMD
from kivymd.uix.list import MDListItemTrailingIcon
# stdlib
import os
import sys
from pathlib import Path
# Custom
from screens.about import About
from screens.settings import Settings
from screens.main_screen import MainScreen
from modules.dialog.exitdialog import ExitDialog
from modules.util.widget_loader import load_widget
from settings.app_settings import GlobalSettings
from api.api_factory import load_apis

APP_DIR = Path(__file__)
print(f"APP_DIR={APP_DIR}")

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    log.info('running in a PyInstaller bundle')
    APP_DIR=Path(__file__).parent
else:
    log.info('running in a normal Python process')
    APP_DIR=Path(__file__).parent.parent

TMP_DIR = APP_DIR / 'tmp'

class SpeechJokey(MDApp):
    def build(self):
        # load_widget(os.path.join(os.path.dirname(loaddialog.__file__), 'loaddialog.kv'))
        # load_widget(os.path.join(os.path.dirname(savedialog.__file__), 'savedialog.kv'))
        # load_widget(os.path.join(os.path.dirname(app_settings.__file__), 'AppSettingsPopup.kv'))
        load_widget(os.path.join(os.path.dirname(
            sys.modules[MainScreen.__module__].__file__), 'main_screen.kv'))
        load_widget(os.path.join(os.path.dirname(
            sys.modules[Settings.__module__].__file__), 'settings.kv'))
        load_widget(os.path.join(os.path.dirname(
            sys.modules[About.__module__].__file__), 'about.kv'))
        load_widget(os.path.join(os.path.dirname(
            sys.modules[ExitDialog.__module__].__file__), 'exitdialog.kv'))
        self.sm = ScreenManager()
        # self.screens = [Screen(name='Title {}'.format(i)) for i in range(4)]
        # self.screens = {
        #     "main": MainScreen(title="Speech Jokey", name="main"),
        #     "settings": Settings(title="Settings", name="settings"),
        #     "about": About(title="About", name="about")
        # }
        self.global_settings = GlobalSettings(APP_DIR, TMP_DIR)
        self.icon = os.path.join(os.curdir, 'speech-jokey.ico')
        Config.set('kivy', 'window_icon', self.icon)
        log.setLevel(LOG_LEVELS["debug"])
        self.apis = load_apis()
        self.api_coqui = self.apis.get("CoquiAPI", None)
        self.sm.add_widget(MainScreen(title="Speech Jokey", name="main"))
        self.settings = Settings(title="Settings", name="settings")
        self.sm.add_widget(self.settings)
        self.settings.setup_apis([self.api_coqui])
        self.sm.add_widget(About(title="About", name="about"))
        return self.sm


if __name__ == '__main__':
    if hasattr(sys, '_MEIPASS'):
        resource_add_path(os.path.join(sys._MEIPASS))
    log.info(f"Using APP_DIR={APP_DIR}")
    log.info(f"Using TMP_DIR={TMP_DIR}")
    os.makedirs(TMP_DIR, exist_ok=True) # This should fix it permanently
    SpeechJokey(kv_file="SpeechJokey.kv").run()
