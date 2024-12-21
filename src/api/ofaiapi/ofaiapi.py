import requests
import os
import base64
import logging as log
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from ..base import BaseApi, BaseApiSettings


class OfaiAPIWidget(MDScreen):
    settings = ObjectProperty(None)
    title = StringProperty("Ofai API Settings")
    api_key_input = ObjectProperty(None)  # Field for the API key input
    voice_selection = ObjectProperty(None)  # Dropdown for selecting voices
    model_selection = ObjectProperty(None)  # Dropdown for selecting models
    voice_names = ListProperty()
    model_names = ListProperty()

    def __init__(self, title: str = "Ofai API Settings", **kwargs):
        super(OfaiAPIWidget, self).__init__(**kwargs)
        self.title = title
        self.name = OfaiAPI.__name__.lower() + "_settings"
        self.voice_names = [voice for voice in OfaiAPI.voices]
        self.model_names = [model for model in OfaiAPI.models]

    def on_leave(self, *args):
        log.info("Leaving Ofai settings screen.")
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


class OfaiAPISettings(BaseApiSettings):
    api_name = "OfaiAPI"
    voice_text = StringProperty("")
    model_text = StringProperty("")

    @classmethod
    def isSupported(cls):
        return True

    @classmethod
    def get_settings_widget(cls):
        return OfaiAPIWidget()

    def __init__(self, widget, **kwargs):
        super(OfaiAPISettings, self).__init__(**kwargs)
        self.widget = widget
        widget.settings = self

        # Bind the text fields in the widget to settings
        self.widget.model_selection.bind(text=self.update_settings)
        self.bind(model_text=self.widget.model_selection.setter('text'))

        self.widget.voice_selection.bind(text=self.update_settings)
        self.bind(voice_text=self.widget.voice_selection.setter('text'))

        self.load_settings()

    def load_settings(self):
        app_instance = App.get_running_app()
        self.voice_text = app_instance.global_settings.get_setting(
            self.api_name, "voice", default="")
        self.model_text = app_instance.global_settings.get_setting(
            self.api_name, "model", default="")

    def save_settings(self):
        app_instance = App.get_running_app()
        app_instance.global_settings.update_setting(
            self.api_name, "voice", self.voice_text)
        app_instance.global_settings.update_setting(
            self.api_name, "model", self.model_text)

    def update_settings(self, instance, value):
        self.model_text = self.widget.model_selection.text
        self.voice_text = self.widget.voice_selection.text


class OfaiAPI(BaseApi):
    models = ["Standard", "Viennese", "Goisern", "Innervillgraten"]
    voices = [
        "Austrian Standard (m)",
        "Viennese (f)",
        "Viennese (m)",
        "young Viennese (f)",
        "Goisern (f1)",
        "Goisern (f2)",
        "Goisern (m1)",
        "Goisern (m2)",
        "Innervillgraten (f1)",
        "Innervillgraten (f2)",
        "Innervillgraten (m1)",
        "Innervillgraten (m2)"
    ]

    def __init__(self, settings: OfaiAPISettings):
        super(OfaiAPI, self).__init__(settings)
        self.settings = settings

    def init_api(self):
        pass

    def reset_api(self):
        pass

    def get_available_model_names(self):
        return self.models

    def text_to_api_format(self, text):
        return text

    def text_from_api_format(self, text):
        return text

    def get_available_voice_names(self):
        return self.voices

    def set_voice_name(self):
        pass

    def get_voice_name(self):
        return self.settings.voice_text

    def synthesize(self, input_text: str, out_filename: str):
        # API-Request
        response = requests.post("https://demo.ofai.at/speech/run/predict", json={
            "data": [
                input_text,
                self.settings.voice_text,
                self.settings.model_text
            ]
        }).json()

        # Check response data
        if "data" in response and response["data"]:
            audio_data_entry = response["data"][0]
            file_name = audio_data_entry.get("name")
            audio_data = audio_data_entry.get("data")

            if audio_data is None and file_name:
                # Download file
                url = f"https://demo.ofai.at/speech/file={file_name}"
                log.info(f"Downloading {url}...")
                response = requests.get(url)
                if response.status_code == 200:
                    with open(out_filename, "wb") as audio_file:
                        audio_file.write(response.content)
                    log.info(f"Successfully downloaded {out_filename}")
                else:
                    log.error(f"Error downloading {response.status_code}")
            elif audio_data:
                # Base64-Daten in WAV-Datei speichern
                log.info("Converting Base64 to WAV...")
                with open(out_filename, "wb") as wav_file:
                    wav_file.write(base64.b64decode(audio_data))
                log.info(f"Successfully saved {out_filename}")
            else:
                log.error("No data found.")
        else:
            log.error("Error processing request.")
