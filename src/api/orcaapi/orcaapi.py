import pvorca
import logging as log
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from ..base import BaseApi, BaseApiSettings


class OrcaAPIWidget(MDScreen):
    settings = ObjectProperty(None)
    title = StringProperty("Orca API Settings")
    api_key_input = ObjectProperty(None)
    region_input = ObjectProperty(None)
    voice_selection = ObjectProperty(None)
    model_selection = ObjectProperty(None)
    voice_names = ListProperty()
    model_names = ListProperty(["standard"])

    def __init__(self, title: str = "Orca API Settings", **kwargs):
        super(OrcaAPIWidget, self).__init__(**kwargs)
        self.title = title
        self.name = OrcaAPI.__name__.lower() + "_settings"
        self.voice_names = [f"{voice['display_name']}" for voice in OrcaAPI.voices]

    def on_leave(self, *args):
        log.info("Leaving Orca settings screen.")
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


class OrcaAPISettings(BaseApiSettings):
    api_name = "OrcaAPI"
    api_key_text = StringProperty("")
    voice_text = StringProperty("")
    model_text = StringProperty("standard")

    @classmethod
    def isSupported(cls):
        return True

    @classmethod
    def get_settings_widget(cls):
        return OrcaAPIWidget()

    def __init__(self, widget, **kwargs):
        super(OrcaAPISettings, self).__init__(**kwargs)
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
            self.api_name, "voice", default="Ingrid (de-AT)")
        self.model_text = app_instance.global_settings.get_setting(
            self.api_name, "model", default="standard")

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


class OrcaAPI(BaseApi):
    voices = [
        {"display_name": "English (female)", "internal_name": "src/api/orcaapi/lib/orca_params_female.pv"},
        {"display_name": "English (male)", "internal_name": "src/api/orcaapi/lib/orca_params_male.pv"}
    ]
    voice_mapping = {voice["display_name"]: voice["internal_name"] for voice in voices}

    def __init__(self, settings: OrcaAPISettings):
        super(OrcaAPI, self).__init__(settings)
        self.settings = settings

    def get_available_voices(self):
        return [voice["display_name"] for voice in self.voices]

    def set_voice(self, display_name):
        # Map the display name to the internal name for synthesis
        internal_name = self.voice_mapping.get(display_name)
        if internal_name:
            self.settings.voice_text = internal_name
            self.settings.save_settings()
        else:
            log.error("Voice not found for display name: %s", display_name)

    def synthesize(self, input_text: str, out_filename: str):
        try:
            orca = pvorca.create(
                access_key=self.settings.widget.ids.api_key_input.text,
                model_path=self.settings.voice_text
            )

            # Text-zu-Sprache-Synthese und Speichern in Datei
            orca.synthesize_to_file(text=input_text, output_path=out_filename)

            # Ressourcen freigeben
            orca.delete()
            log.info(f"Successfully saved {out_filename}")
        except Exception as e:
            log.error(f"Orca Sdk synthesize error: {e}")
