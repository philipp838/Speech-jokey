from pathlib import Path
import openai
from openai import OpenAI
import logging as log
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from ..base import BaseApi, BaseApiSettings


class OpenAIAPIWidget(MDScreen):
    settings = ObjectProperty(None)
    title = StringProperty("OpenAI API Settings")
    api_key_input = ObjectProperty(None)  # Field for the API key input
    voice_selection = ObjectProperty(None)  # Dropdown for selecting voices
    model_selection = ObjectProperty(None)  # Dropdown for selecting models
    voice_names = ListProperty(["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
    model_names = ListProperty(["tts-1", "tts-1-hd"])

    def __init__(self, title: str = "OpenAI API Settings", **kwargs):
        super(OpenAIAPIWidget, self).__init__(**kwargs)
        self.title = title
        self.name = OpenAIAPI.__name__.lower() + "_settings"

    def on_leave(self, *args):
        log.info("Leaving OpenAI settings screen.")
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


class OpenAIAPISettings(BaseApiSettings):
    api_name = "OpenAIAPI"
    api_key_text = StringProperty("")
    voice_text = StringProperty("alloy")
    model_text = StringProperty("tts-1")

    @classmethod
    def isSupported(cls):
        return True

    @classmethod
    def get_settings_widget(cls):
        return OpenAIAPIWidget()

    def __init__(self, widget, **kwargs):
        super(OpenAIAPISettings, self).__init__(**kwargs)
        self.widget = widget
        widget.settings = self

        # Bind the text fields in the widget to settings
        self.widget.api_key_input.bind(text=self.update_settings)
        self.bind(api_key_text=self.widget.api_key_input.setter('text'))

        self.widget.model_selection.bind(text=self.update_settings)
        self.bind(model_text=self.widget.model_selection.setter('text'))

        self.widget.voice_selection.bind(text=self.update_settings)
        self.bind(voice_text=self.widget.voice_selection.setter('text'))

        self.load_settings()

    def load_settings(self):
        app_instance = App.get_running_app()
        self.api_key_text = app_instance.global_settings.get_setting(
            self.api_name, "api_key", default="")
        self.voice_text = app_instance.global_settings.get_setting(
            self.api_name, "voice", default="alloy")
        self.model_text = app_instance.global_settings.get_setting(
            self.api_name, "model", default="tts-1")

    def save_settings(self):
        app_instance = App.get_running_app()
        app_instance.global_settings.update_setting(
            self.api_name, "api_key", self.api_key_text)
        app_instance.global_settings.update_setting(
            self.api_name, "voice", self.voice_text)
        app_instance.global_settings.update_setting(
            self.api_name, "model", self.model_text)

    def update_settings(self, instance, value):
        self.api_key_text = self.widget.api_key_input.text
        self.model_text = self.widget.model_selection.text
        self.voice_text = self.widget.voice_selection.text


class OpenAIAPI(BaseApi):
    _models = ["tts-1", "tts-1-hd"]
    _voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    def __init__(self, settings: OpenAIAPISettings):
        super(OpenAIAPI, self).__init__(settings)
        self.settings = settings
        self.init_api()

    def init_api(self):
        self.settings.load_settings()
        openai.api_key = self.settings.api_key_text

    def get_available_voices(self):
        return self._voices

    def set_voice(self, voice_name):
        self.settings.voice_text = voice_name
        self.settings.save_settings()
        self.init_api()

    def get_models(self):
        return self._models

    def synthesize(self, input_text: str, out_filename: str):
        self.init_api()  # Ensure API key is loaded
        if not input_text:
            raise ValueError("Input must not be empty")

        try:
            # Initialize the OpenAI client with the API key
            client = OpenAI(api_key=self.settings.api_key_text)

            # Make the API request for audio synthesis
            response = client.audio.speech.create(
                model=self.settings.model_text,
                voice=self.settings.voice_text,
                input=input_text
            )

            # Write the audio content to the specified file
            with open(out_filename, "wb") as f:
                f.write(response.content)

            log.info(f"Audio successfully saved to {out_filename}")

        except Exception as e:
            log.error(f"Error during synthesis: {e}")
            raise
