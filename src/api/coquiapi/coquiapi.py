import torch
from TTS.api import TTS
import logging as log
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from ..base import BaseApi, BaseApiSettings

device = "cuda" if torch.cuda.is_available() else "cpu"


class CoquiAPIWidget(MDScreen):
    settings = ObjectProperty(None)
    title = StringProperty("Coqui API Settings")
    api_key_input = ObjectProperty(None)  # Field for the API key input
    voice_selection = ObjectProperty(None)  # Dropdown for selecting voices
    model_selection = ObjectProperty(None)  # Dropdown for selecting models
    voice_names = ListProperty()
    model_names = ListProperty(["standard"])

    def __init__(self, title: str = "Coqui API Settings", **kwargs):
        super(CoquiAPIWidget, self).__init__(**kwargs)
        self.title = title
        self.name = CoquiAPI.__name__.lower() + "_settings"
        self.voice_names = [f"{voice['display_name']}" for voice in CoquiAPI.voices]

    def on_leave(self, *args):
        log.info("Leaving Coqui settings screen.")
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


class CoquiAPISettings(BaseApiSettings):
    api_name = "CoquiAPI"
    voice_text = StringProperty("")
    model_text = StringProperty("standard")

    @classmethod
    def isSupported(cls):
        return True

    @classmethod
    def get_settings_widget(cls):
        return CoquiAPIWidget()

    def __init__(self, widget, **kwargs):
        super(CoquiAPISettings, self).__init__(**kwargs)
        self.widget = widget
        widget.settings = self

        self.widget.voice_selection.bind(text=self.update_settings)
        self.bind(voice_text=self.widget.voice_selection.setter('text'))

        self.load_settings()

    def load_settings(self):
        app_instance = App.get_running_app()
        self.voice_text = app_instance.global_settings.get_setting(
            self.api_name, "voice", default="")
        self.model_text = app_instance.global_settings.get_setting(
            self.api_name, "model", default="standard")

    def save_settings(self):
        app_instance = App.get_running_app()
        app_instance.global_settings.update_setting(
            self.api_name, "voice", self.voice_text)

    def update_settings(self, instance, value):
        self.voice_text = self.widget.voice_selection.text


class CoquiAPI(BaseApi):
    voices = [
        {"display_name": "Vits (de)", "internal_name": "tts_models/de/thorsten/vits", "speaker_type": "single"},

        {"display_name": "Tortoise (en)", "internal_name": "tts_models/en/multi-dataset/tortoise-v2", "speaker_type": "single"},

        {"display_name": "YourTTS (en-female1)", "internal_name": "tts_models/multilingual/multi-dataset/your_tts--female-en-5", "speaker_type": "multi", "lang": "en"},
        {"display_name": "YourTTS (en-female2)", "internal_name": "tts_models/multilingual/multi-dataset/your_tts--female-en-5\n", "speaker_type": "multi", "lang": "en"},
        {"display_name": "YourTTS (en-male1)", "internal_name": "tts_models/multilingual/multi-dataset/your_tts--male-en-2", "speaker_type": "multi", "lang": "en"},
        {"display_name": "YourTTS (en-male2)", "internal_name": "tts_models/multilingual/multi-dataset/your_tts--male-en-2\n", "speaker_type": "multi", "lang": "en"},
        {"display_name": "YourTTS (pt-female)", "internal_name": "tts_models/multilingual/multi-dataset/your_tts--female-pt-4\n", "speaker_type": "multi", "lang": "pt-br"},
        {"display_name": "YourTTS (pt-male)", "internal_name": "tts_models/multilingual/multi-dataset/your_tts--male-pt-3\n", "speaker_type": "multi", "lang": "pt-br"},
        {"display_name": "YourTTS (fr-female)", "internal_name": "tts_models/multilingual/multi-dataset/your_tts--female-en-5\n", "speaker_type": "multi", "lang": "fr-fr"},
        {"display_name": "YourTTS (fr-male)", "internal_name": "tts_models/multilingual/multi-dataset/your_tts--male-en-2\n", "speaker_type": "multi", "lang": "fr-fr"}
    ]
    xtts_v2_lang = ['de', 'en', 'es', 'fr', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh-cn', 'hu', 'ko', 'ja', 'hi']
    xtts_v2_speaker = ['Claribel Dervla', 'Daisy Studious', 'Gracie Wise', 'Tammie Ema', 'Alison Dietlinde', 'Ana Florence',
                       'Annmarie Nele', 'Asya Anara', 'Brenda Stern',  'Gitta Nikolina', 'Henriette Usha', 'Sofia Hellen',
                       'Tammy Grit', 'Tanja Adelina', 'Vjollca Johnnie', 'Andrew Chipper', 'Badr Odhiambo', 'Dionisio Schuyler',
                       'Royston Min', 'Viktor Eka', 'Abrahan Mack', 'Adde Michal', 'Baldur Sanjin', 'Craig Gutsy', 'Damien Black',
                       'Gilberto Mathias', 'Ilkin Urbano', 'Kazuhiko Atallah', 'Ludvig Milivoj', 'Suad Qasim', 'Torcull Diarmuid',
                       'Viktor Menelaos', 'Zacharie Aimilios', 'Nova Hogarth', 'Maja Ruoho', 'Uta Obando', 'Lidiya Szekeres',
                       'Chandra MacFarland', 'Szofi Granger', 'Camilla Holmström', 'Lilya Stainthorpe', 'Zofija Kendrick',
                       'Narelle Moon', 'Barbora MacLean', 'Alexandra Hisakawa', 'Alma María', 'Rosemary Okafor', 'Ige Behringer',
                       'Filip Traverse', 'Damjan Chapman', 'Wulf Carlevaro', 'Aaron Dreschner', 'Kumar Dahl', 'Eugenio Mataracı',
                       'Ferran Simen', 'Xavier Hayasaka', 'Luis Moray', 'Marcos Rudaski']

    for lang in xtts_v2_lang:
        for speaker in xtts_v2_speaker:
            voices.append({
                "display_name": f"{speaker} ({lang})",
                "internal_name": f"tts_models/multilingual/multi-dataset/xtts_v2--{speaker}",
                "speaker_type": "multi",
                "lang": lang
            })

    voice_mapping = {voice["display_name"]: voice["internal_name"] for voice in voices}

    def __init__(self, settings: CoquiAPISettings):
        super(CoquiAPI, self).__init__(settings)
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
            # Get current voice from display name
            selected_voice = next(
                (v for v in self.voices if v["internal_name"] == self.settings.voice_text), None
            )

            if not selected_voice:
                log.error("Selected voice not found.")
                return

            # Multilinguale Unterstützung prüfen
            speaker_type = selected_voice.get("speaker_type", None)
            lang = selected_voice.get("lang", None)

            # Get model
            model = self.settings.voice_text.split("--")[0]
            tts = TTS(model_name=model).to(device)

            if speaker_type == "single":
                tts.tts_to_file(
                    text=input_text,
                    file_path=out_filename
                )

            elif speaker_type == "multi" and lang:
                speaker = self.settings.voice_text.split("--")[-1]
                # Provide speaker and language for multilanguage voice
                tts.tts_to_file(
                    text=input_text,
                    speaker=speaker,
                    language=lang,
                    file_path=out_filename
                )

            log.info(f"Audio successfully saved to {out_filename}")

        except Exception as e:
            log.error(f"Error during synthesis: {e}")
            raise
