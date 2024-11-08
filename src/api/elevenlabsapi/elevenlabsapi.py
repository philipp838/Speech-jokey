try:
    from elevenlabs import stream, save
    from elevenlabs.client import ElevenLabs
except ImportError:
    raise ImportError(
        "Please install elevenlabs module: pip install elevenlabs (for installation details: https://github.com/elevenlabs/elevenlabs-python)")

if __name__ == '__main__':
    import argparse
import logging
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivy.logger import Logger as log
from kivymd.uix.screen import MDScreen
from typing import List
from ..base import BaseApiSettings, BaseApi
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown

class ElevenLabsAPIWidget(MDScreen):
    settings = ObjectProperty(None)
    title = StringProperty()
    # property values shown in widget
    api_key_input = ObjectProperty(None)
    voice_selection = ObjectProperty(None)
    model_selection = ObjectProperty(None)
    voice_names = ListProperty()
    model_names = ListProperty()

    def __init__(self, title: str = "ElevenLabs API Settings", **kwargs):
        super(ElevenLabsAPIWidget, self).__init__(**kwargs)
        self.title = title
        self.name = ElevenLabsAPI.__name__.lower() + "_settings"

    def transit(self, target: str, direction: str):
        log.info("Transitioning to %s, direction: %s", target, direction)
        self.manager.transition.direction = direction
        self.manager.current = target

    def transit_to_self(self):
        log.info("Transitioning to self")
        self.transit(self.name, 'right')

    # Will be called, when settings widget is left.
    def on_leave(self, *args):
        log.info("on_leave of settings")
        self.settings.save_settings()

    # Initializes the API and tests the validity of the API key.
    def init_api(self):
        try:
            self.settings.update_settings(self.api_key_input, self.api_key_input.text)
            self.settings.save_settings()
            api_name = "ElevenLabsAPI"
            app_instance = App.get_running_app()
            app_instance.apis.get(api_name, None).reset_api()
            app_instance.apis.get(api_name, None).init_api()
            log.info("API key valid.")
        except:
            log.error("API key invalid.")
    
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

# Represents the model of the widget class (view).
# Contains the current settings values, which should be used by the API.
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
        # Changes in widget, update settings object
        self.widget.api_key_input.bind(text=self.update_settings)
        # Changes in settings object, update widget
        self.bind(api_key_text=self.widget.api_key_input.setter('text'))

        # Two-way bindings between widget properties and settings properties
        # Changes in widget, update settings object
        self.widget.model_selection.bind(text=self.update_settings)
        # Changes in settings object, update widget
        self.bind(model_text=self.widget.model_selection.setter('text'))

        # Changes in widget, update settings object
        self.widget.voice_selection.bind(text=self.update_settings)
        # Changes in settings object, update widget
        self.bind(voice_text=self.widget.voice_selection.setter('text'))

        self.load_settings()

    # loads the settings from the settings file.
    def load_settings(self):
        app_instance = App.get_running_app()
        self.api_key_text = app_instance.global_settings.get_setting(
            self.api_name, "api_key", default="")
        self.voice_text = app_instance.global_settings.get_setting(
            self.api_name, "voice", default="")
        self.model_text = app_instance.global_settings.get_setting(
            self.api_name, "model", default="")

    # saves the settings to the settings file.
    def save_settings(self):
        app_instance = App.get_running_app()
        app_instance.global_settings.update_setting(
            self.api_name, "api_key", self.api_key_text)
        app_instance.global_settings.update_setting(
            self.api_name, "voice", self.voice_text)
        app_instance.global_settings.update_setting(
            self.api_name, "model", self.model_text)

    # Updates the settings: Stores current values of the widget properties in the settings properties.
    def update_settings(self, instance, value):
        log.info("updating %s=%s",instance, value)
        app_instance = App.get_running_app()

        # if API key changed, reinit the API
        if not self.api_key_text == self.widget.api_key_input.text:
            self.api_key_text=self.widget.api_key_input.text
            app_instance.apis.get(self.api_name, None).reset_api()

        self.model_text=self.widget.model_selection.text
        self.voice_text=self.widget.voice_selection.text
        #self.save_settings()

class ElevenLabsAPI(BaseApi):
    def __init__(self, settings: ElevenLabsAPISettings = None):
        super(ElevenLabsAPI, self).__init__(settings)
        logging.debug("Initializing ElevenLabsAPI instance...")
        self.settings = settings
        self.elevenlabs_ref = None
        # Caching of voices and models
        self.voices=[]
        self.models=[]

    # Resets the API instance. So that the next use of the API will reinitialize it.
    def reset_api(self):
        self.elevenlabs_ref=None
        self.voices=[]
        self.models=[]
        self.settings.widget.voice_names=[]
        self.settings.widget.model_names=[]

    # Initializes the API instance with the API key from the settings.
    def init_api(self):
        if self.elevenlabs_ref is not None:
            log.debug("API already initialized with key: %s", self.settings.api_key_text)
            return # Already initialized

        self.settings.load_settings()
        # Try to init the API.
        # This will only work, if the settings are configured properly.
        try:
            log.debug("Initializing with API key: %s", self.settings.api_key_text)
            self.elevenlabs_ref=ElevenLabs(api_key=self.settings.api_key_text)
            self.settings.widget.model_names=self.get_available_model_names()
            self.settings.widget.voice_names=self.get_available_voice_names()
            log.info("Elevenlabs API initialized.")
        except:
            log.error("API Key invalid: %s",self.settings.api_key_text)
            raise

    # Returns a list of available voice object instances.
    def get_available_voices(self):
        """
        get list of available voices
        """

        if len(self.voices) == 0:
            log.debug("Fetching voices from API")
            try:
                self.init_api()
                self.voices=self.elevenlabs_ref.voices.get_all().voices
            except Exception as e:
                log.error(f"get_available_voices: {e}")
                self.voices=[]

        return self.voices

    # Returns a list of available model object instances.
    def get_available_models(self):
        """
        get list of available models
        """
        log.debug(f"self.models: {self.models}")
        if len(self.models) == 0:
            try:
                self.init_api()
                self.models=self.elevenlabs_ref.models.get_all()
            except Exception as e:
                log.error(f"get_available_models: {e}")
                self.models=[]

        return self.models

    def get_available_voice_names(self) -> List[str]:
        try:
            voice_names=[voice.name for voice in self.get_available_voices()]
            log.info(f"Available voice_names: {voice_names}")
            return voice_names
        except Exception as e:
            log.error(f"get_available_voice_names: {e}")
            return []

    # Returns a list of available model names.
    def get_available_model_names(self) -> List[str]:
        try:
            return [model.model_id for model in self.get_available_models() if model.can_do_text_to_speech]
        except Exception as e:
            log.error(f"get_available_model_names: {e}")
            return []

    # Sets the active voice name and saves the settings.
    def set_voice_name(self, voice_name):
        self.settings.voice_text=voice_name
        self.settings.save_settings()

    # Convert the text to a format that the ElevenLabs API can process. This can be converting from simple text to SSML.
    def text_to_api_format(self, text: str):
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

    def text_from_api_format(self, text):
        raise NotImplementedError("text_from_api_format not implemented")
        pass

    # Synthesize the input text using the ElevenLabs API.
    def synthesize(self, input: str, out_filename: str = None):
        """
        Synthesize an input using the ElevenLabs TTS API.

        Args:
            sentence (str): sentence to be synthesized
            out_filename (str): output filename (Optional, if not provided, the audio will be played instead of saved)
        """
        print(input)
        self.init_api()

        if (not input):
            raise ValueError("Input must not be empty")

        shouldStream = True if not out_filename else False
        self.voice = next((v for v in self.get_available_voices() if v.name ==
                           self.settings.voice_text), None)
        self.model = self.settings.model_text
        #set_api_key(self.settings.api_key_text)

        # TODO: hier neuer Teil
        converted_input = self.text_to_api_format(input)

        try:
            audio = self.elevenlabs_ref.generate(text=converted_input, voice=self.voice,
                             model=self.model, stream=shouldStream)
            if (shouldStream):
                stream(audio)
            else:
                save(audio, out_filename)
        except Exception as e:
            log.error(f"synthesize: {e}")
            raise Exception(e.body['detail']['message'])

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
    voice_names=tts.get_available_voice_names()
    print(voice_names)

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

    tts.play()
