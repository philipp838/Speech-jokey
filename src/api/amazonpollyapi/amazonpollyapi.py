import os
from pathlib import Path
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import logging as log
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from ..base import BaseApi, BaseApiSettings


class AmazonPollyAPIWidget(MDScreen):
    settings = ObjectProperty(None)
    title = StringProperty("Amazon Polly API Settings")
    access_key_id_input = ObjectProperty(None)  # Field for access key ID input
    secret_access_key_input = ObjectProperty(None)  # Field for secret access key input
    voice_selection = ObjectProperty(None)  # Dropdown for selecting voices
    model_selection = ObjectProperty(None)  # Dropdown for selecting models
    voice_names = ListProperty()
    model_names = ListProperty(["standard"])

    def __init__(self, title: str = "Amazon Polly API Settings", **kwargs):
        super(AmazonPollyAPIWidget, self).__init__(**kwargs)
        self.title = title
        self.name = AmazonPollyAPI.__name__.lower() + "_settings"
        # Set voice_names from the available voices in AmazonPollyAPI
        self.voice_names = [f"{voice['display_name']}" for voice in AmazonPollyAPI.voices]

    def on_leave(self, *args):
        log.info("Leaving Amazon Polly settings screen.")
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


class AmazonPollyAPISettings(BaseApiSettings):
    api_name = "AmazonPollyAPI"
    access_key_id_text = StringProperty("")
    secret_access_key_text = StringProperty("")
    voice_text = StringProperty("Vicky")
    model_text = StringProperty("standard")

    @classmethod
    def isSupported(cls):
        return True

    @classmethod
    def get_settings_widget(cls):
        return AmazonPollyAPIWidget()

    def __init__(self, widget, **kwargs):
        super(AmazonPollyAPISettings, self).__init__(**kwargs)
        self.widget = widget
        widget.settings = self

        # Bind the text fields in the widget to settings (correct references)
        self.widget.access_key_id_input.bind(text=self.update_settings)
        self.bind(access_key_id_text=self.widget.access_key_id_input.setter('text'))
        self.widget.secret_access_key_input.bind(text=self.update_settings)
        self.bind(secret_access_key_text=self.widget.secret_access_key_input.setter('text'))
        self.widget.model_selection.bind(text=self.update_settings)
        self.bind(model_text=self.widget.model_selection.setter('text'))
        self.widget.voice_selection.bind(text=self.update_settings)
        self.bind(voice_text=self.widget.voice_selection.setter('text'))

        self.load_settings()

    def load_settings(self):
        app_instance = App.get_running_app()
        # Load other settings if needed, like voice and model
        self.access_key_id_text = app_instance.global_settings.get_setting(
            self.api_name, "access_key_id_input", default="")
        self.secret_access_key_text = app_instance.global_settings.get_setting(
            self.api_name, "secret_access_key_input", default="")
        self.voice_text = app_instance.global_settings.get_setting(
            self.api_name, "voice", default="Vicky")
        self.model_text = app_instance.global_settings.get_setting(
            self.api_name, "model", default="standard")

    def save_settings(self):
        app_instance = App.get_running_app()
        app_instance.global_settings.update_setting(
            self.api_name, "access_key_id_input", self.access_key_id_text)
        app_instance.global_settings.update_setting(
            self.api_name, "secret_access_key_input", self.secret_access_key_text)
        app_instance.global_settings.update_setting(
            self.api_name, "voice", self.voice_text)
        app_instance.global_settings.update_setting(
            self.api_name, "model", self.model_text)

    def update_settings(self, instance, value):
        self.access_key_id_text = self.widget.access_key_id_input.text
        self.secret_access_key_text = self.widget.secret_access_key_input.text
        self.voice_text = self.widget.voice_selection.text
        self.model_text = self.widget.model_selection.text


class AmazonPollyAPI(BaseApi):
    # Define available voices with display names and internal identifiers
    voices = [
        {"display_name": "Vicki (de-DE)", "internal_name": "Vicki", "language": "de-DE"},
        {"display_name": "Marlene (de-DE)", "internal_name": "Marlene", "language": "de-DE"},
        {"display_name": "Hans (de-DE)", "internal_name": "Hans", "language": "de-DE"},
        {"display_name": "Salli (en-US)", "internal_name": "Salli", "language": "en-US"},
        {"display_name": "Kimberly (en-US)", "internal_name": "Kimberly", "language": "en-US"},
        {"display_name": "Justin (en-US)", "internal_name": "Justin", "language": "en-US"},
        {"display_name": "Joey (en-US)", "internal_name": "Joey", "language": "en-US"},
        {"display_name": "Emma (en-GB)", "internal_name": "Emma", "language": "en-GB"},
        {"display_name": "Brian (en-GB)", "internal_name": "Brian", "language": "en-GB"},
        {"display_name": "Amy (en-GB)", "internal_name": "Amy", "language": "en-GB"},
        {"display_name": "Raveena (en-IN)", "internal_name": "Raveena", "language": "en-IN"},
        {"display_name": "Aditi (en-IN)", "internal_name": "Aditi", "language": "en-IN"}
    ]

    # Create a mapping for quick lookup of internal names by display name
    voice_mapping = {voice["display_name"]: voice["internal_name"] for voice in voices}

    def __init__(self, settings: AmazonPollyAPISettings):
        super(AmazonPollyAPI, self).__init__(settings)
        self.settings = settings
        self.init_api()

    def init_api(self):
        # Load settings if needed for other configurations
        self.settings.load_settings()

        # Access the TextInput fields from the settings widget
        access_key_id_input = self.settings.widget.ids.access_key_id_input.text
        secret_access_key_input = self.settings.widget.ids.secret_access_key_input.text

        # Initialize a boto3 session with the provided credentials
        self.session = boto3.session.Session(
            aws_access_key_id=access_key_id_input,
            aws_secret_access_key=secret_access_key_input,
            region_name="eu-north-1"
        )

        # Create the Polly client from the session
        self.polly_client = self.session.client("polly")

    def get_available_voices(self):
        # Return only the display names
        return [voice["display_name"] for voice in self.voices]

    def set_voice(self, display_name):
        # Map the display name to the internal name for synthesis
        internal_name = self.voice_mapping.get(display_name)
        if internal_name:
            self.settings.voice_text = internal_name
            self.settings.save_settings()
        else:
            log.error("Voice not found for display name: %s", display_name)

    def synthesize(self, input_text: str, out_filename: str, text_type="text"):
        try:
            response = self.polly_client.synthesize_speech(
                Text=input_text,
                TextType=text_type,
                OutputFormat="mp3",
                VoiceId=self.settings.voice_text
            )

            # Ensure audio stream exists and save to file
            if "AudioStream" in response:
                with open(out_filename, "wb") as file:
                    file.write(response["AudioStream"].read())
            else:
                log.error("AudioStream not found in the response.")

        except (BotoCoreError, ClientError) as error:
            log.error(f"An error occurred: {error}")
            raise
