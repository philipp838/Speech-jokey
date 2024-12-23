from typing import List

import select
from gtts import gTTS
import logging as log
from kivymd.uix.screen import MDScreen
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from ..base import BaseApi, BaseApiSettings


class GttsAPIWidget(MDScreen):
    settings = ObjectProperty(None)
    title = StringProperty("gTTS Settings")
    voice_selection = ObjectProperty(None)
    voice_names = ListProperty()

    def __init__(self, title: str = "gTTS Settings", **kwargs):
        super(GttsAPIWidget, self).__init__(**kwargs)
        self.title = title
        self.name = GttsAPI.__name__.lower() + "_settings"
        # Stimmen laden und der voice_names-Liste hinzufügen
        self.voice_names = [voice['display_name'] for voice in GttsAPI.voices]

    def on_leave(self, *args):
        log.info("Leaving gTTS settings screen.")
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


class GttsAPISettings(BaseApiSettings):
    api_name = "GttsAPI"
    voice_text = StringProperty("")
    lang_text = StringProperty("")

    @classmethod
    def isSupported(cls):
        return True

    @classmethod
    def get_settings_widget(cls):
        return GttsAPIWidget()

    def __init__(self, widget, **kwargs):
        super(GttsAPISettings, self).__init__(**kwargs)
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

    def save_settings(self):
        app_instance = App.get_running_app()
        app_instance.global_settings.update_setting(
            self.api_name, "voice", self.voice_text)

    def update_settings(self, instance, value):
        self.voice_text = self.widget.voice_selection.text


class GttsAPI(BaseApi):
    voices = []
    local_accents = {
        'Deutsch (Deutschland)': {'lang': 'de'},
        'English (Australia)': {'lang': 'en', 'tld': 'com.au'},
        'English (United Kingdom)': {'lang': 'en', 'tld': 'co.uk'},
        'English (United States)': {'lang': 'en', 'tld': 'us'},
        'English (Canada)': {'lang': 'en', 'tld': 'ca'},
        'English (India)': {'lang': 'en', 'tld': 'co.in'},
        'English (Ireland)': {'lang': 'en', 'tld': 'ie'},
        'English (South Africa)': {'lang': 'en', 'tld': 'co.za'},
        'English (Nigeria)': {'lang': 'en', 'tld': 'com.ng'},
        'French (Canada)': {'lang': 'fr', 'tld': 'ca'},
        'French (France)': {'lang': 'fr', 'tld': 'fr'},
        'Mandarin (China Mainland)': {'lang': 'zh-CN'},
        'Mandarin (Taiwan)': {'lang': 'zh-TW'},
        'Portuguese (Brazil)': {'lang': 'pt', 'tld': 'com.br'},
        'Portuguese (Portugal)': {'lang': 'pt', 'tld': 'pt'},
        'Spanish (Mexico)': {'lang': 'es', 'tld': 'com.mx'},
        'Spanish (Spain)': {'lang': 'es', 'tld': 'es'},
        'Spanish (United States)': {'lang': 'es', 'tld': 'us'},
    }

    for accent, config in local_accents.items():
        if "tld" in config:
            internal_name = f"{config['lang']}-{config['tld']}"
        else:
            internal_name = config['lang']
        voices.append({
            "display_name": accent,
            "internal_name": internal_name,
        })

    def __init__(self, settings: GttsAPISettings):
        super(GttsAPI, self).__init__(settings)
        self.settings = settings
        self.init_api()

    def init_api(self):
        self.settings.load_settings()
        pass

    def reset_api(self):
        pass

    def get_available_model_names(self):
        return []

    def text_to_api_format(self, text):
        return text

    def text_from_api_format(self, text):
        return text

    def get_available_voice_names(self):
        return [voice["display_name"] for voice in self.voices]

    def set_voice_name(self, display_name):
        # Search voice using display_name
        selected_voice = next(
            (v for v in self.voices if v["display_name"] == display_name), None
        )
        if selected_voice:
            log.info(f"Voice set to: {display_name}")
            self.settings.voice_text = selected_voice["display_name"]
            self.settings.save_settings()
        else:
            log.error("Voice not found for display name: %s", display_name)

    def get_voice_name(self):
        selected_voice = self.__get_selected_voice()
        return selected_voice["display_name"] if selected_voice != None else ""

    def synthesize(self, input_text: str, out_filename: str):
        if not input_text:
            log.error("Input text must not be empty.")
            return

        selected_voice=self.__get_selected_voice()
        if not selected_voice:
            log.error("Selected voice not found.")
            return

        lang = selected_voice['internal_name'].split('-')[0]
        tld = selected_voice['internal_name'].split('-')[1] if '-' in selected_voice['internal_name'] else None

        try:
            if tld:
                tts = gTTS(text=input_text, lang=lang, tld=tld)
            else:
                tts = gTTS(text=input_text, lang=lang)
            tts.save(out_filename)
        except Exception as e:
            log.error(f"Error during synthesis: {e}")

    def __get_selected_voice(self):
        selected_voice = next(
            (v for v in self.voices if v['display_name'] == self.settings.voice_text), None
        )
        return selected_voice
