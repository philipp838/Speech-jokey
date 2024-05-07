try:
    from elevenlabs import voices, generate, play, save, set_api_key, get_api_key, VoiceSettings
except ImportError:
    raise ImportError(
        "Please install elevenlabs module: pip install elevenlabs (for installation details: https://github.com/elevenlabs/elevenlabs-python)")

if __name__ == '__main__':
    import argparse
import logging
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivy.logger import Logger as log
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.expansionpanel import MDExpansionPanel
from pathlib import Path
from typing import Iterator, List
from ..base import BaseApiSettings
import os
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from pydub import AudioSegment          # TODO: add pydub to dependencies


ELEVENLABS_API_KEY = "8eb906f48ad066d589328ce0c579d265"

# If API key is not set, prompt the user to enter it
if not get_api_key():
    set_api_key(ELEVENLABS_API_KEY)
    log.info("API key is set to default value.")


class ElevenLabsAPIWidget(MDExpansionPanel):
    api_key_input = ObjectProperty(None)
    voice_selection = ObjectProperty(None)
    model_selection = ObjectProperty(None)
    voice_names = ListProperty()
    model_names = ListProperty()
    settings = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ElevenLabsAPIWidget, self).__init__(**kwargs)
        self.settings = ElevenLabsAPISettings(self)

        # Initialize api_key_input as a TextInput
        self.api_key_input = TextInput(
            hint_text='Enter API Key', multiline=False)
        self.add_widget(self.api_key_input)
        
        # Two-way bind api-key
        self.api_key_input.bind(text=self.settings.setter('api_key_text'))
        self.settings.bind(api_key_text=self.api_key_input.setter('text'))

        # Initialize voice_selection as CustomSpinner
        self.voice_selection = CustomSpinner(options=self.voice_names)
        self.add_widget(self.voice_selection)

        # Initialize model_selection as CustomSpinner
        self.model_selection = CustomSpinner(options=self.model_names)
        self.add_widget(self.model_selection)

        # Set environment variable for token
        self.api_key_input.bind(on_text_validate=self.update_api_key)
        
        # Two-way bind model
        self.model_selection.bind(text=self.settings.setter('model_text'))
        self.settings.bind(model_text=self.model_selection.setter('text'))
        
        self.settings.load_settings()

    def update_api_key(self, instance, value):
        self.settings.api_key_text = value

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
        self.dropdown.bind(on_select=lambda instance,
                           x: setattr(self, 'text', x))


class ElevenLabsAPISettings(BaseApiSettings):
    api_name = 'ElevenLabsAPI'
    api_key_text = StringProperty('')
    voice_text = StringProperty('')
    model_text = StringProperty('')
    widget = ObjectProperty(None)

    @classmethod
    def isSupported(cls):
        return True

    @classmethod
    def get_settings_widget(cls):
        return ElevenLabsAPIWidget()

    def __init__(self, widget: ElevenLabsAPIWidget, **kwargs):
        super(ElevenLabsAPISettings, self).__init__(**kwargs)
        self.widget = widget

        self.load_settings()

    def load_settings(self):
        app_instance = App.get_running_app()
        self.api_key_text = app_instance.global_settings.get_setting(
            self.api_name, "api_key", default=ELEVENLABS_API_KEY)
        self.voice_text = app_instance.global_settings.get_setting(
            self.api_name, "voice", default="Serena")
        self.model_text = app_instance.global_settings.get_setting(
            self.api_name, "model", default="multilingual v2")
        self.api = ElevenLabsAPI(self)
        app_instance.api = self.api

        # Update de widget UI-elementen nadat de instellingen zijn geladen
        if self.widget and self.widget.api_key_input:
            self.widget.api_key_input.text = self.api_key_text
        else:
            log.error("api_key_input is not correctly initialized.")

        if self.widget and self.widget.voice_selection:
            self.widget.voice_selection.text = self.voice_text

        if self.widget and self.widget.model_selection:
            self.widget.model_selection.text = self.model_text

    def save_settings(self):
        app_instance = App.get_running_app()
        app_instance.global_settings.update_setting(
            self.api_name, "api_key", self.api_key_text)
        app_instance.global_settings.update_setting(
            self.api_name, "voice", self.voice_text)
        app_instance.global_settings.update_setting(
            self.api_name, "model", self.model_text)

    def on_api_key_entered(self):
        new_api_key = self.widget.api_key_input.text
        log.info("New API key entered: %s", new_api_key)

        # update API-key in settings
        self.settings.api_key_text = new_api_key
        self.settings.save_settings()

        log.info("Settings updated with new API key.")
    def update_api_key(self, instance, value):
        print("update_api_key called")
        print("New API key value:", value)
        self.api_key_text = value
        self.save_settings()

class ElevenLabsAPI():
    _models = [
        "eleven_multilingual_v2",
        "eleven_monolingual_v1"
    ]

    def __init__(self, settings: ElevenLabsAPISettings = None, api_key: str = ELEVENLABS_API_KEY, voice_name: str = 'Serena', model: str = "eleven_multilingual_v2"):
        logging.debug("Initializing ElevenLabsAPI instance...")
        self.settings = settings
        if settings is None:
            if model not in self._models:
                raise ValueError(
                    f'Model not supported: {model} (must be one of: {", ".join(self._models)})')
            if (not api_key):
                api_key = get_api_key()
                if (not api_key):
                    raise ValueError(
                        "No API key provided and no API key found in environment variable (ELEVENLABS_API_KEY)")
            else:
                set_api_key(api_key)

            # print("API key:", get_api_key())
            # print("Voice name:", voice_name)
            # print("Model:", model)


            self.voice = next(
                (v for v in voices() if v.name == voice_name), None)
            if (not self.voice):
                raise ValueError(
                    f'Voice not found: {voice_name} (available voices: {", ".join(v.name for v in voices())})')
            self.model = model
        else:
            # print("API key:", get_api_key())
            # print("Voice name:", voice_name)
            # print("Model:", model)

            self.settings = settings

    def get_available_voices(self):
        """
        Haal een lijst met beschikbare stemnamen op van de API.
        """
        # Implementeer logica om stemnamen op te halen van de API
        # Dit kan een HTTP-verzoek naar de API zijn of het ophalen van stemnamen uit een lokaal bestand of database
        # Retourneer een lijst met stemnamen
        # Dit is een voorbeeld, vervang dit door de echte implementatie
        return [voice.name for voice in voices()]

    def synthesize(self, input: str, out_filename: str = None):
        """
        Synthesize an input using the ElevenLabs TTS API.

        Args:
            sentence (str): sentence to be synthesized
            out_filename (str): output filename (Optional, if not provided, the audio will be played instead of saved)
        """
        print(input)
        if (not input):
            raise ValueError("Input must not be empty")
        shouldStream = True if not out_filename else False
        if self.settings is None:
            text = input, voice = self.voice, model = self.model, stream = shouldStream
            self.generate(text, voice, model, stream)
            print(text)
            if (shouldStream):
                print("this is the shouldstream")
                play(audio)
            else:
                save(audio, out_filename)
        else:
            self.voice = next((v for v in voices() if v.name ==
                               self.settings.voice_text), None)
            self.model = self._models[0]
            set_api_key(self.settings.api_key_text)
            audio = generate(text=input, voice=self.voice,
                             model=self.model, stream=shouldStream)
            if (shouldStream):
                play(audio)
            else:
                save(audio, out_filename)
    def play(self, input: str):
        """
        method plays audio file, that is saved in the 'tmp' folder.
        """
        print("playing...")
        # Placeholder implementation
        src_path = str(Path(os.path.dirname(__file__)).parents[2])
        tmp_path = os.path.join(src_path, 'tmp')
        print(tmp_path)
        if len(os.listdir(tmp_path)) == 0:
            print("Directory is empty. Press generate first!")
        else:
            audio_path = os.path.join(tmp_path, 'output_file.wav')        # name of your audio file
            print(audio_path)
            audio = AudioSegment.from_wav(audio_path)
            play(audio)
    @staticmethod
    def get_config():
        return {
            "api_key": str,
            "language": str,
            "voice": str
        }

    @staticmethod
    def get_models() -> List[str]:
        return ElevenLabsAPI._models

    @staticmethod
    def get_voices() -> List[str]:
        return [v.name for v in voices()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filename",
                        help="Output filename", default=None)
    args = parser.parse_args()

    # Create an instance of ElevenLabsAPISettings
    api_settings = ElevenLabsAPISettings()

    # Load settings
    api_settings.load_settings()

    # Create an instance of ElevenLabsAPI with the correct settings
    api_key = api_settings.api_key_text
    tts = ElevenLabsAPI(api_settings, api_key)

    # Use the synthesize method with the desired input and output filename
    tts.synthesize(input="""
    Dear Natascha,

    I hope you are doing well! I just wanted to give you a quick update on our project, the SpeechJokey application. We have a small yet exciting update!

    We've been working on a class template that communicates with the ElevenLabs API. It's still in an early phase and more of a playground at the moment, but it's a step in the right direction. The aim is for you to find your own path as a DJ using a synthetic voice with this application.

    It's a small progress, but an important one. We are still experimenting and trying to fine-tune everything for you. Your thoughts and ideas on this are, as always, very welcome.

    Look forward to more as we make further advancements!

    Best regards,

    Serena the AI voice
    """, out_filename=args.filename)
