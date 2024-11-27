import pyttsx3
import re
import logging as log
from kivymd.uix.screen import MDScreen
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from ..base import BaseApi, BaseApiSettings


class Pyttsx3APIWidget(MDScreen):
    settings = ObjectProperty(None)
    title = StringProperty("Pyttsx3 Settings")
    voice_selection = ObjectProperty(None)
    voice_names = ListProperty()
    model_names = ListProperty(["standard"])

    def __init__(self, title: str = "Pyttsx3 Settings", **kwargs):
        super(Pyttsx3APIWidget, self).__init__(**kwargs)
        self.title = title
        self.name = Pyttsx3API.__name__.lower() + "_settings"
        # Stimmen laden und der voice_names-Liste hinzufügen
        Pyttsx3API.initialize_voices()
        self.voice_names = [voice['display_name'] for voice in Pyttsx3API.voices]

    def on_leave(self, *args):
        log.info("Leaving Pyttsx3 settings screen.")
        if self.settings:
            self.settings.save_settings()

    def get_current_voice(self):
        return self.voice_selection.text


class CustomSpinner(Button):
    def __init__(self, options, **kwargs):
        super().__init__(**kwargs)
        self.options = options
        self.dropdown = DropDown()
        for option in self.options:
            btn = Button(text=option, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: self.dropdown.select(btn.text))
            self.dropdown.add_widget(btn)
        self.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(self, 'text', x))


class Pyttsx3APISettings(BaseApiSettings):
    api_name = "Pyttsx3API"
    voice_text = StringProperty("")
    lang_text = StringProperty("")

    @classmethod
    def isSupported(cls):
        return True

    @classmethod
    def get_settings_widget(cls):
        return Pyttsx3APIWidget()

    def __init__(self, widget, **kwargs):
        super(Pyttsx3APISettings, self).__init__(**kwargs)
        self.widget = widget
        widget.settings = self

        # Bind the voice selection dropdown to the settings
        self.widget.voice_selection.bind(text=self.update_settings)
        self.bind(voice_text=self.widget.voice_selection.setter('text'))

        self.load_settings()

    def load_settings(self):
        app_instance = App.get_running_app()
        self.voice_text = app_instance.global_settings.get_setting(
            self.api_name, "voice", default="")
        self.lang_text = app_instance.global_settings.get_setting(
            self.api_name, "language", default="")

    def save_settings(self):
        app_instance = App.get_running_app()
        app_instance.global_settings.update_setting(
            self.api_name, "voice", self.voice_text)
        app_instance.global_settings.update_setting(
            self.api_name, "language", self.lang_text)

    def update_settings(self, instance, value):
        self.voice_text = self.widget.voice_selection.text


class Pyttsx3API(BaseApi):
    voices = []

    @classmethod
    def initialize_voices(cls):
        if not cls.voices:  # Only initialize once
            engine = pyttsx3.init()
            available_voices = engine.getProperty('voices')
            for voice in available_voices:
                cls.voices.append({
                    "display_name": voice.name,
                    "internal_name": voice.id,
                })

    def __init__(self, settings: Pyttsx3APISettings):
        super(Pyttsx3API, self).__init__(settings)
        self.settings = settings
        # Ensure voices are initialized before use
        Pyttsx3API.initialize_voices()

    def get_available_voices(self):
        return [voice["display_name"] for voice in self.voices]

    def set_voice(self, display_name):
        matching_voice = next((v for v in self.voices if v["display_name"] == display_name), None)
        if matching_voice:
            self.settings.voice_text = matching_voice["internal_name"]
            self.settings.save_settings()
        else:
            log.error("Voice not found: %s", display_name)

    def synthesize(self, input_text: str, out_filename: str):
        if not input_text:
            log.info("Input text must not be empty.")

        engine = pyttsx3.init()
        engine.setProperty('voice', self.settings.voice_text)

        try:
            engine.save_to_file(input_text, out_filename)
            engine.runAndWait()
            log.info(f"Audio successfully saved to {out_filename}")
        except Exception as e:
            log.error(f"Error during synthesis: {e}")
            raise
        finally:
            engine.stop()  # Ensures the engine is shut down properly
