try:
    from elevenlabs import voices, generate, play, save, set_api_key, get_api_key, VoiceSettings
except ImportError:
    raise ImportError(
        "Please install elevenlabs module: pip install elevenlabs (for installation details: https://github.com/elevenlabs/elevenlabs-python)")

if __name__ == '__main__':
    import argparse
import logging
import dotenv
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivy.logger import Logger as log
from kivymd.uix.screen import MDScreen
from pathlib import Path
from typing import Iterator, List
from ..base import BaseApiSettings
import os
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from pydub import AudioSegment
from pydub.playback import play as pyplay
import tkinter.filedialog as fd


from dotenv import load_dotenv
load_dotenv(override=True)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    print(
        "No API-Key set: Please make a file called '.env'. In there write: ELEVENLABS_API_KEY = [your API key] OR add your API key in the application settings.")

# TODO: for that to work you have to make a file called '.env_'. In there write: ELEVENLABS_API_KEY = [your API key]
# TODO: see how that can be generated automatically on project setup!!

# If API key is not set, prompt the user to enter it
if not get_api_key():
    set_api_key(ELEVENLABS_API_KEY)
    log.info("API key is set to default value.")


class ElevenLabsAPIWidget(MDScreen):
    settings = ObjectProperty(None)
    title = StringProperty()
    api_key_input = ObjectProperty(None)
    voice_selection = ObjectProperty(None)
    model_selection = ObjectProperty(None)
    voice_names = ListProperty()
    model_names = ListProperty()

    def __init__(self, title: str = "ElevenLabs API Settings", **kwargs):
        super(ElevenLabsAPIWidget, self).__init__(**kwargs)
        self.title = title
        self.name = ElevenLabsAPI.__name__.lower() + "_settings"

    def update_api_key(self, value):
        self.settings.api_key_text = value

    def transit(self, target: str, direction: str):
        self.manager.transition.direction = direction
        self.manager.current = target

    def transit_to_self(self):
        self.transit(self.name, 'right')


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
    api_name = "ElevenLabsAPI"
    # NOTE ElevenLabs API SETTING properties (not to be mistaken with the properties of the widget, holding current selections)
    api_key_text = StringProperty("")
    voice_text = StringProperty("")
    model_text = StringProperty("")

    @classmethod
    def isSupported(cls):
        return True

    @classmethod
    def get_settings_widget(cls):
        return ElevenLabsAPIWidget()

    def __init__(self, widget: ElevenLabsAPIWidget, **kwargs):
        super(ElevenLabsAPISettings, self).__init__(**kwargs)
        self.widget = widget  # Save reference to the widget
        widget.settings = self  # Set the settings object in the widget
        # Two-way bind api-key
        widget.api_key_input.bind(text=self.setter('api_key_text'))
        self.bind(api_key_text=self.widget.api_key_input.setter('text'))

        # Binding to update environment variable with input API key
        widget.api_key_input.bind(on_text_validate=self.update_api_key)

        # Two-way bind model
        self.widget.model_selection.bind(text=self.setter('model_text'))
        self.bind(model_text=self.widget.model_selection.setter('text'))
        self.load_settings()

    def load_settings(self):
        app_instance = App.get_running_app()
        self.api_key_text = app_instance.global_settings.get_setting(
            self.api_name, "api_key", default=ELEVENLABS_API_KEY)
        self.voice_text = app_instance.global_settings.get_setting(
            self.api_name, "voice", default="Serena")
        self.model_text = app_instance.global_settings.get_setting(
            self.api_name, "model", default="multilingual v2")

        # Update de widget UI-elementen nadat de instellingen zijn geladen
        # if self.widget and self.widget.api_key_input:
        #     self.widget.api_key_input.text = self.api_key_text
        # else:
        #     log.error("api_key_input is not correctly initialized.")

        # if self.widget and self.widget.voice_selection:
        #     self.widget.voice_selection.text = self.voice_text

        # if self.widget and self.widget.model_selection:
        #     self.widget.model_selection.text = self.model_text

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
        self.update_api_key(new_api_key)
        self.settings.save_settings()

        log.info("Settings updated with new API key.")

    def update_api_key(self, value: str):
        new_api_key = self.widget.api_key_input.text
        print("update_api_key called")
        print("New API key value:", new_api_key)
        self.api_key_text = new_api_key
        self.save_settings()
        dotenv_file = dotenv.find_dotenv()
        dotenv.load_dotenv(dotenv_file)
        # print("heeeeh",os.environ["ELEVENLABS_API_KEY"])
        os.environ["ELEVENLABS_API_KEY"] = new_api_key
        # print("heeeeh2",os.environ["ELEVENLABS_API_KEY"])
        dotenv.set_key(dotenv_file, "ELEVENLABS_API_KEY",
                       os.environ["ELEVENLABS_API_KEY"])


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
        get list of available voices
        """
        # Implementeer logica om stemnamen op te halen van de API
        # Dit kan een HTTP-verzoek naar de API zijn of het ophalen van stemnamen uit een lokaal bestand of database
        # Retourneer een lijst met stemnamen
        # Dit is een voorbeeld, vervang dit door de echte implementatie
        return [voice.name for voice in voices()]

    # neue Funktion
    def convert_text(self, text: str):
        text_arr = list(text)
        output_text = ""
        for char in text_arr:
            # print(char)
            if char == ",":  # default pause
                output_text = output_text + "<break time=\"0.0s\" />"

            elif char == "." or char == "?" or char == "!":
                output_text = output_text + "<break time=\"0.5s\" />"

            elif char == ";":
                output_text = output_text + "<break time=\"0.5s\" />"

            output_text = output_text + char
        return output_text

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

            audio = self.generate(text, voice, model, stream)
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

            # TODO: hier neuer Teil
            converted_input = self.convert_text(input)

            audio = generate(text=converted_input, voice=self.voice,
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
            # name of your audio file
            audio_path = os.path.join(tmp_path, 'output_file.wav')
            print(audio_path)
            try:
                audio = AudioSegment.from_file(audio_path, "mp3")
            except:
                audio = AudioSegment.from_file(audio_path, format="mp4")

            pyplay(audio)
    def save(): 
        """
        now you can choose where to save the file .
        """
        pass 

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
