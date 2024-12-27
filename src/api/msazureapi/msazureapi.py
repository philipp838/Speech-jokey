import requests
import azure.cognitiveservices.speech as speechsdk
import logging as log
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from ..base import BaseApi, BaseApiSettings


class MSAzureAPIWidget(MDScreen):
    settings = ObjectProperty(None)
    title = StringProperty("Microsoft Azure API Settings")
    api_key_input = ObjectProperty(None)
    region_input = ObjectProperty(None)
    voice_selection = ObjectProperty(None)
    voice_names = ListProperty()

    def __init__(self, title: str = "Microsoft Azure API Settings", **kwargs):
        super(MSAzureAPIWidget, self).__init__(**kwargs)
        self.title = title
        self.name = MSAzureAPI.__name__.lower() + "_settings"
        self.voice_names = [f"{voice['display_name']}" for voice in MSAzureAPI.voices]

    def on_leave(self, *args):
        log.info("Leaving OpenAI settings screen.")
        if self.settings:
            self.settings.save_settings()

    def get_current_voice(self):
        return self.voice_selection.text

    def init_api(self):
        self.settings.update_settings(self.api_key_input, self.api_key_input.text)
        self.settings.save_settings()
        app_instance = App.get_running_app()
        api_name = "MSAzureAPI"
        app_instance.api_factory.get_api(api_name).reset_api()
        app_instance.api_factory.get_api(api_name).init_api()
        if self.__check_azure_api_key():
            log.info("Microsoft Azure API key valid.")
        else:
            log.error("Microsoft Azure API key invalid.")

    def __check_azure_api_key(self):
        endpoint = f"https://{self.settings.region_text}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        headers = {
            "Ocp-Apim-Subscription-Key": self.settings.api_key_text
        }

        try:
            # Send a POST request to the token endpoint
            response = requests.post(endpoint, headers=headers)

            # Check if the response status is 200 (OK)
            if response.status_code == 200:
                return True
            else:
                print(f"Invalid API key or error: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error while connecting to Azure Speech API: {e}")
            return False


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


class MSAzureAPISettings(BaseApiSettings):
    api_name = "MSAzureAPI"
    api_key_text = StringProperty("")
    voice_text = StringProperty("Ingrid (de-AT)")
    region_text = StringProperty("")
    lang_text = StringProperty("")

    @classmethod
    def isSupported(cls):
        return True

    @classmethod
    def get_settings_widget(cls):
        return MSAzureAPIWidget()

    def __init__(self, widget, **kwargs):
        super(MSAzureAPISettings, self).__init__(**kwargs)
        self.widget = widget
        widget.settings = self

        # Bind the text fields in the widget to settings
        self.widget.api_key_input.bind(text=self.update_settings)
        self.bind(api_key_text=self.widget.api_key_input.setter('text'))

        self.widget.voice_selection.bind(text=self.update_settings)
        self.bind(voice_text=self.widget.voice_selection.setter('text'))

        self.widget.region_input.bind(text=self.update_settings)
        self.bind(region_text=self.widget.region_input.setter('text'))

        self.load_settings()

    def load_settings(self):
        app_instance = App.get_running_app()

        self.api_key_text = app_instance.global_settings.get_setting(
            self.api_name, "api_key", default="")
        self.region_text = app_instance.global_settings.get_setting(
            self.api_name, "region", default="")
        self.lang_text = app_instance.global_settings.get_setting(
            self.api_name, "language", default="")
        self.voice_text = app_instance.global_settings.get_setting(
            self.api_name, "voice", default=""
        )
        matching_voice = next(
            (v["display_name"] for v in MSAzureAPI.voices if v["internal_name"] == self.voice_text),
            None
        )
        if matching_voice:
            self.widget.voice_selection.text = matching_voice
        else:
            log.warning(f"No matching display name for internal name: {self.voice_text}")

    def save_settings(self):
        app_instance = App.get_running_app()
        app_instance.global_settings.update_setting(
            self.api_name, "api_key", self.api_key_text)
        app_instance.global_settings.update_setting(
            self.api_name, "voice", self.voice_text)
        app_instance.global_settings.update_setting(
            self.api_name, "region", self.region_text)
        app_instance.global_settings.update_setting(
            self.api_name, "language", self.lang_text)

    def update_settings(self, instance, value):
        self.api_key_text = self.widget.api_key_input.text
        self.region_text = self.widget.region_input.text

        selected_voice = next(
            (v for v in MSAzureAPI.voices if v["display_name"] == self.widget.voice_selection.text),
            None
        )
        if selected_voice:
            self.voice_text = selected_voice["internal_name"]
            log.info(f"Saved internal_name: {self.voice_text}")


class MSAzureAPI(BaseApi):
    voices = [
        {"display_name": "Ingrid (de-AT)", "internal_name": "de-AT-IngridNeural", "language": "de-AT"},
        {"display_name": "Jonas (de-AT)", "internal_name": "de-AT-JonasNeural", "language": "de-AT"},
        {"display_name": "Seraphina (de-DE)", "internal_name": "de-DE-SeraphinaMultilingualNeural", "language": "de-DE"},
        {"display_name": "Florian (de-DE)", "internal_name": "de-DE-FlorianMultilingualNeural", "language": "de-DE"},
        {"display_name": "Katja (de-DE)", "internal_name": "de-DE-KatjaNeural", "language": "de-DE"},
        {"display_name": "Leni (de-CH)", "internal_name": "de-CH-LeniNeural", "language": "de-CH"},
        {"display_name": "Jan (de-CH)", "internal_name": "de-CH-JanNeural", "language": "de-CH"},
        {"display_name": "Ava (en-US)", "internal_name": "en-US-AvaMultilingualNeural", "language": "en-US"},
        {"display_name": "Andrew (en-US)", "internal_name": "en-US-AndrewMultilingualNeural", "language": "en-US"},
        {"display_name": "Derek (en-US)", "internal_name": "en-US-DerekMultilingualNeural", "language": "en-US"},
        {"display_name": "Ada (en-GB)", "internal_name": "en-GB-AdaMultilingualNeural", "language": "en-GB"},
        {"display_name": "Libby (en-GB)", "internal_name": "en-GB-LibbyNeural", "language": "en-GB"},
        {"display_name": "Ryan (en-GB)", "internal_name": "en-GB-RyanNeural", "language": "en-GB"}
    ]
    voice_mapping = {voice["display_name"]: voice["internal_name"] for voice in voices}

    ssml_tags = {
        "⏸️": ('<break time="2s"/>', ""),
        "😐": ("<emphasis level=\"reduced\">", "</emphasis>"),
        "🙂": ("<emphasis level=\"moderate\">", "</emphasis>"),
        "😁": ("<emphasis level=\"strong\">", "</emphasis>"),
        "🔈": ("<prosody volume=\"silent\">", "</prosody>"),
        "🔉": ("<prosody volume=\"medium\">", "</prosody>"),
        "🔊": ("<prosody volume=\"loud\">", "</prosody>"),
        "🌏": ("<lang xml:lang=\"en-US\">", "</lang>")
    }

    def __init__(self, settings: MSAzureAPISettings):
        super(MSAzureAPI, self).__init__(settings)
        self.settings = settings

    def init_api(self):
        self.settings.load_settings()

    def reset_api(self):
        self.voices = []
        self.settings.widget.voice_names = []

    def get_available_model_names(self):
        return []

    def text_to_api_format(self, text):
        return text

    def text_from_api_format(self, text):
        return text

    def get_available_voice_names(self):
        return [voice["display_name"] for voice in self.voices]

    def get_voice_name(self):
        selected_voice = self.__get_selected_voice()
        return selected_voice["display_name"]

    def set_voice_name(self, display_name):
        # Map the display name to the internal name and save it
        internal_name = self.voice_mapping.get(display_name)
        if internal_name:
            self.settings.voice_text = internal_name
            voice_info = next((voice for voice in self.voices if voice["internal_name"] == self.settings.voice_text), None)
            if voice_info:
                self.settings.lang_text = voice_info["language"]
                self.settings.save_settings()
            else:
                log.error("Language not found for voice: %s", self.settings.voice_text)
            self.settings.save_settings()
        else:
            log.error("Voice not found for display name: %s", display_name)

    def set_language(self):
        # Find the language for the selected voice
        selected_voice = self.settings.voice_text
        voice_info = next((voice for voice in self.voices if voice["internal_name"] == selected_voice), None)

        if voice_info:
            self.settings.lang_text = voice_info["language"]
            self.settings.save_settings()
        else:
            log.error("Language not found for voice: %s", selected_voice)

    def emoji_to_ssml_tag(self, text: str, ssml_tags: dict):
        """
        Convert emojis in the text to Azure-compatible SSML tags.
        """
        voice = self.settings.voice_text
        self.set_language()
        lang = self.settings.lang_text

        ssml_text = f"<speak version='1.0' xml:lang='{lang}'><voice name='{voice}'>"
        for emoji, tags in ssml_tags.items():
            open_tag, close_tag = tags
            if close_tag:  # For emojis with both open and close tags
                text = text.replace(emoji, open_tag, 1)  # Replace first occurrence with open tag
                text = text.replace(emoji, close_tag, 1)  # Replace next occurrence with close tag
            else:  # For self-closing tags
                text = text.replace(emoji, open_tag)
        ssml_text += text + "</voice></speak>"

        return ssml_text

    def synthesize(self, input_text: str, file_path: str):
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.settings.api_key_text,
            region=self.settings.region_text
        )
        self.speech_config.speech_synthesis_voice_name = self.settings.voice_text

        # Synthesize the speech
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)

        processed_text = self.emoji_to_ssml_tag(input_text, self.ssml_tags)
        result = synthesizer.speak_ssml_async(processed_text).get()

        # Check the result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # Save the audio data to a file
            stream = speechsdk.AudioDataStream(result)
            stream.save_to_wav_file(file_path)
            log.info(f"Audio successfully saved to {file_path}")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    print("Error details: {}".format(cancellation_details.error_details))
                    print("Did you set the speech resource key and region values?")

    def __get_selected_voice(self):
        selected_voice = next(
            (v for v in self.voices if v['internal_name'] == self.settings.voice_text), None
        )
        return selected_voice
