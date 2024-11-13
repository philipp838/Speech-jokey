# Kivy
from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty
from kivy.core.text import LabelBase
from kivy.logger import Logger as log
# KivyMD
from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.filemanager import MDFileManager
from kivy.uix.popup import Popup
# stdlib
import os
import time
# Custom
from modules.dialog.exitdialog import ExitDialog
# Pdf and .docx to text conversion
import fitz  # PyMuPDF
import docx2txt
from docx import Document
# Audio playback
from pygame import mixer

# Register fonts
font_path = os.path.join(os.path.dirname(__file__), "../../fonts/Symbola.ttf")
LabelBase.register(name="symbola", fn_regular=font_path)


class EmojiPopup(Popup):
    def __init__(self, text_input, **kwargs):
        super(EmojiPopup, self).__init__(**kwargs)
        self.text_input = text_input
        # Access the shared ssml tags dictionary from MainScreen
        self.ssml_tags = MainScreen.ssml_tags
        # Track the state for each emoji
        self.tag_state = {emoji: "open" for emoji in self.ssml_tags.keys()}

    # Old method to place emoji in textfield
    def insert_emoji(self, emoji):
        # Get cursor position
        cursor_index = self.text_input.cursor_index()

        # Divide the current text of the text input into two parts:
        # Text before and after cursor position
        current_text = self.text_input.text
        new_text = (
            current_text[:cursor_index] +  # Text in front of cursor
            emoji +                        # The emoji to be inserted
            current_text[cursor_index:]    # Text after cursor
        )

        # Set the new text in the TextInput
        self.text_input.text = new_text

        # Place the cursor behind the inserted emoji
        self.text_input.cursor = (cursor_index + len(emoji), 0)

        self.dismiss()


class MainScreen(MDScreen):
    title = StringProperty()
    current_engine_text = StringProperty("tts engine: \nElevenLabs")
    text_input = ObjectProperty(None)
    text_type = StringProperty("text")
    voice_dialog = None
    selected_voice = StringProperty()
    # FIXME The values of this dictionary needs to be kept in sync with the screen names in main.py (Unfortunately)
    menu_options = {
        "Settings": "settings",
        "About": "about",
        "Exit": None  # NOTE Exit just closes the app and doesn't have an associated screen
    }
    ssml_tags = {
        "🗣️": ("<speak>", "</speak>"),
        "⏸️": ('<break time="2s"/>', ""),
        "😐": ("<emphasis level=\"reduced\">", "</emphasis>"),
        "🙂": ("<emphasis level=\"moderate\">", "</emphasis>"),
        "😁": ("<emphasis level=\"strong\">", "</emphasis>"),
        "🔈": ("<prosody volume=\"silent\">", "</prosody>"),
        "🔉": ("<prosody volume=\"medium\">", "</prosody>"),
        "🔊": ("<prosody volume=\"loud\">", "</prosody>"),
        "🌏": ("<lang xml:lang=\"en-US\">", "</lang>")
    }
    supported_text_files = ["txt", "md", "rst", "pdf", "docx"]

    def __init__(self, title: str, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.title = title
        # Initialize the current TTS engine text
        self.update_current_engine_text()
        self.last_path = None
        self.opened_file = None

        # Bind each TTS API's voice setting to automatically update the selected_voice on change
        app = App.get_running_app()
        if hasattr(app, 'api_elevenlabs'):
            app.api_elevenlabs.settings.bind(voice_text=self.update_current_voice)
        #if hasattr(app, 'api_openai'):
            #app.api_openai.settings.bind(voice_text=self.update_current_voice)
        #if hasattr(app, 'api_amazonpolly'):
            #app.api_amazonpolly.settings.bind(voice_text=self.update_current_voice)
        #if hasattr(app, 'api_msazure'):
            #app.api_msazure.settings.bind(voice_text=self.update_current_voice)

        # FIXME This is used to keep track of the file manager state (open or closed) but is not currently used
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            icon_selection_button="folder-marker"
        )
        # TODO Adjust the scrollbar within MDFileManager to be more visible (not just a thin line)

        # new: for cursor movement and selection of words
        self.cnt_button = 0
        self.old_cnt_button = 0
        self.old_cursor_index = self.ids.text_main.cursor_index()
        Clock.schedule_once(self.set_focus, 0.1)
        self.load_current_voice()
        app.api_elevenlabs.settings.bind(voice_text=self.update_current_voice)

    def check_for_ssml_content(self):
        """
        Check if the text contains any SSML-related emojis and set text_type accordingly.
        """
        input_text = self.ids.text_main.text
        ssml_emojis = self.ssml_tags.keys()

        # If any emoji in ssml_emojis is found in the input text, set text_type to "ssml"
        if any(emoji in input_text for emoji in ssml_emojis):
            self.text_type = "ssml"
        else:
            self.text_type = "text"

    def amazon_emoji_to_ssml_tag(self, text):
        for emoji, tags in self.ssml_tags.items():
            open_tag, close_tag = tags
            if close_tag:  # For emojis with both open and close tags
                text = text.replace(emoji, open_tag, 1)  # First occurrence as open tag
                text = text.replace(emoji, close_tag, 1)  # Next occurrence as close tag
            else:  # For self-closing tags
                text = text.replace(emoji, open_tag)

        return text

    def msazure_emoji_to_ssml_tag(self, text):
        """
        Convert emojis in the text to Azure-compatible SSML tags.
        """
        app = App.get_running_app()
        api = app.api_msazure
        voice = api.settings.voice_text

        app.api_msazure.set_language()
        lang = api.settings.lang_text

        ssml_text = f"<speak version='1.0' xml:lang='{lang}'><voice name='{voice}'>"
        for emoji, tags in self.ssml_tags.items():
            open_tag, close_tag = tags
            if close_tag:  # For emojis with both open and close tags
                text = text.replace(emoji, open_tag, 1)  # Replace first occurrence with open tag
                text = text.replace(emoji, close_tag, 1)  # Replace next occurrence with close tag
            else:  # For self-closing tags
                text = text.replace(emoji, open_tag)
        ssml_text += text + "</voice></speak>"

        return ssml_text

    def on_ssml_button_click(self):
        try:
            log.debug("%s: SSML button pressed", self.__class__.__name__)
            emoji_popup = EmojiPopup(self.ids.text_main)
            emoji_popup.open()
        except Exception as e:
            log.error("%s: Error with SSML button: %s", self.__class__.__name__, e)

    def load_current_voice(self):
        app_instance = App.get_running_app()
        current_engine = self.get_current_tts_engine()

        # Retrieve the default voice for the selected engine from global settings
        if current_engine == "ElevenLabs":
            self.selected_voice = app_instance.global_settings.get_setting("ElevenLabsAPI", "voice", default="Serena")
        elif current_engine == "OpenAI":
            self.selected_voice = app_instance.global_settings.get_setting("OpenAIAPI", "voice", default="Echo")
        elif current_engine == "Amazon Polly":
            self.selected_voice = app_instance.global_settings.get_setting("AmazonPollyAPI", "voice", default="Vicki")
        elif current_engine == "Microsoft Azure":
            self.selected_voice = app_instance.global_settings.get_setting("MSAzureAPI", "voice", default="Ingrid (de-AT)")
        else:
            self.selected_voice = ""  # Fallback if no engine is set

    def update_current_voice(self, instance, value):
        self.selected_voice = value if value is not None else ""
        self.ids.btn_select_voice.text = f"current voice:\n{self.selected_voice}"

    def on_menu_open(self):
        menu_items = [
            {
                "text": option,
                "on_release": lambda x=option: self.menu_callback(x),
            } for option in self.menu_options.keys()
        ]
        self.drop_menu = MDDropdownMenu(
            caller=self.ids.btn_menu, items=menu_items
        )
        self.drop_menu.open()

    def menu_callback(self, text_item):
        self.manager.transition.direction = 'left'
        if text_item not in self.menu_options.keys():
            log.error("%s: Invalid menu option: %s",
                      self.__class__.__name__, text_item)
            return
        if text_item == "Exit":
            ExitDialog().open()
        self.manager.current = self.menu_options[text_item]
        self.drop_menu.dismiss()

    def select_path(self, path):
        log.info("%s: Selected path: %s", self.__class__.__name__, path)
        if os.path.isfile(path):
            self.opened_file = os.path.basename(path)
            self.last_path = os.path.dirname(path)
            log.debug("%s: File: %s - Path: %s", self.__class__.__name__,
                      self.opened_file, self.last_path)
        elif os.path.isdir(path):
            self.last_path = path
        else:
            log.error("%s: Invalid path selected: %s",
                      self.__class__.__name__, path)
        self.exit_manager()

    def exit_manager(self, *args):
        if all([self.last_path, self.opened_file]):
            file = os.path.join(self.last_path, self.opened_file)
            self.load_text_from_file(file)
        else:
            log.error("%s: No file selected. Last path: %s",
                      self.__class__.__name__, self.last_path)
        self.manager_open = False
        self.file_manager.close()

    def pdf_to_text(self, file_path):
        text = ""
        try:
            pdf_document = fitz.open(file_path)
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                text += page.get_text()
            pdf_document.close()
        except Exception as e:
            log.error("%s: Error reading PDF file: %s. Exception: %s",
                      self.__class__.__name__, file_path, e)
        return text

    def docx_to_text(self, file_path):
        text = ""
        try:
            text = docx2txt.process(file_path)
        except Exception as e:
            log.error("%s: Error reading DOCX file: %s. Exception: %s",
                      self.__class__.__name__, file_path, e)
        return text

    def save_docx_text(self, file_path, text):
        try:
            # Open the existing document
            document = Document(file_path)

            # Overwrite content like in text file
            for _ in range(len(document.paragraphs)):
                p = document.paragraphs[0]
                p._element.getparent().remove(p._element)

            # Write text to document
            for line in text.split('\n'):
                document.add_paragraph(line)

            # Save document
            document.save(file_path)
            log.info("%s: Saved DOCX file: %s", self.__class__.__name__, file_path)
        except Exception as e:
            log.error("%s: Error saving DOCX file: %s. Exception: %s",
                      self.__class__.__name__, file_path, e)

    def on_load_file(self):
        if self.last_path is not None:
            path = self.last_path
        else:
            path = os.path.expanduser("~")
        self.file_manager.show(path)
        self.manager_open = True

    def on_save_file(self):
        if self.last_path is None or self.opened_file is None:
            log.error("%s: No file opened to save.", self.__class__.__name__)
            return
        file = os.path.join(self.last_path, self.opened_file)
        file_ext = os.path.splitext(file)[1][1:].lower()

        if file_ext == "docx":
            self.save_docx_text(file, self.ids.text_main.text)
        elif file_ext == "pdf":
            log.info("%s: Saving Pdfs not supported yet.", self.__class__.__name__)
        else:
            self.save_textfile(file)

    def load_text_from_file(self, file: str):
        if file is None:
            log.error("%s: No file selected to load.", self.__class__.__name__)
            return
        if not os.path.isfile(file):
            log.error("%s: Selection is not a file: %s",
                      self.__class__.__name__, file)
            return
        file_ext = os.path.splitext(file)[1][1:].lower()

        if file_ext not in self.supported_text_files:
            log.error("%s: Unsupported file type: %s. Supported types: %s",
                      self.__class__.__name__, file_ext, self.supported_text_files)
            self.opened_file = None
            self.ids.text_main.text = ""
            return

        try:
            if file_ext == "pdf":
                text = self.pdf_to_text(file)
            elif file_ext == "docx":
                text = self.docx_to_text(file)
            else:  # For txt, md, rst
                with open(os.path.abspath(file), 'r') as f:
                    text = f.read()

            self.ids.text_main.text = text
            log.info("%s: Loaded file: %s", self.__class__.__name__, file)
            log.debug("%s: Text: %s...", self.__class__.__name__, text[0:40])
        except Exception as e:
            log.error("%s: Error loading file: %s. Exception: %s",
                      self.__class__.__name__, file, e)

    def save_textfile(self, file: str):
        if file is None:
            log.error("%s: No file selected to save.", self.__class__.__name__)
            return
        with open(os.path.abspath(file), 'w') as file:
            file.write(self.ids.text_main.text)
            log.info("%s: Saved file: %s", self.__class__.__name__, file)

    def get_current_tts_engine(self):
        # Retrieve the current TTS engine from global settings
        app = App.get_running_app()
        current_engine = app.global_settings.get_setting("TTS", "current_engine", default="ElevenLabs")
        return current_engine

    def update_current_engine_text(self):
        # Update the property with the current engine text
        self.current_engine_text = f"tts engine: \n{self.get_current_tts_engine()}"

    def on_select_tts_engine(self):
        app = App.get_running_app()
        available_engines = {
            "ElevenLabs": app.api_elevenlabs,
            "OpenAI": app.api_openai,
            "Amazon Polly": app.api_amazonpolly,
            "Microsoft Azure": app.api_msazure
        }

        # Prepare menu items for each available TTS engine
        menu_items = [
            {
                "text": engine_name,
                "on_release": lambda x=engine_name: self.select_tts_engine(x),
            } for engine_name in available_engines.keys()
        ]

        # Create and open the dropdown menu
        self.engine_dropdown_menu = MDDropdownMenu(
            caller=self.ids.btn_select_engine,
            items=menu_items,
            width_mult=4
        )
        self.engine_dropdown_menu.open()

    def select_tts_engine(self, engine_name):
        log.info("Selected TTS engine: %s", engine_name)
        app = App.get_running_app()

        self.selected_engine = engine_name
        self.ids.btn_select_engine.text = f"tts engine:\n{engine_name}"

        # Retrieve the current voice for the selected engine
        if engine_name == "ElevenLabs":
            self.selected_voice = app.api_elevenlabs.settings.voice_text
        elif engine_name == "OpenAI":
            self.selected_voice = app.api_openai.settings.voice_text
        elif engine_name == "Amazon Polly":
            self.selected_voice = app.api_amazonpolly.settings.voice_text
        elif engine_name == "Microsoft Azure":
            self.selected_voice = app.api_msazure.settings.voice_text
        else:
            self.selected_voice = "N/A"

        # Update the current voice display
        self.ids.btn_select_voice.text = f"current voice:\n{self.selected_voice}"

        # Update the selected TTS engine in global settings or any relevant setting location
        app.global_settings.update_setting("TTS", "current_engine", engine_name)

        # Update the button text to display the selected engine
        self.update_current_engine_text()

        # Dismiss the dropdown menu
        self.engine_dropdown_menu.dismiss()

    def on_select_voice(self):
        app = App.get_running_app()
        current_engine = self.get_current_tts_engine()

        # Determine which API to use based on the current engine
        if current_engine == "ElevenLabs":
            api = app.api_elevenlabs
        elif current_engine == "OpenAI":
            api = app.api_openai
        elif current_engine == "Amazon Polly":
            api = app.api_amazonpolly
        elif current_engine == "Microsoft Azure":
            api = app.api_msazure
        else:
            log.error("Unknown TTS engine selected.")
            return

        # Get available voices from the selected API
        if api:
            voice_names = api.get_available_voices()
            if voice_names:
                # Create dropdown menu items for each available voice
                menu_items = [
                    {
                        "text": voice_name,  # Display the formatted voice name
                        "on_release": lambda x=voice_name: self.select_voice(x),
                    } for voice_name in voice_names
                ]
                # Create and open the dropdown menu for voice selection
                self.voice_dropdown_menu = MDDropdownMenu(
                    caller=self.ids.btn_select_voice,
                    items=menu_items,
                    width_mult=4,
                )
                self.voice_dropdown_menu.open()
            else:
                log.error("%s: No voices available for the selected TTS engine.", self.__class__.__name__)
        else:
            log.error("%s: API not available for the selected TTS engine.", self.__class__.__name__)

    def select_voice(self, voice_name):
        log.info("Selected voice: %s", voice_name)
        current_engine = self.get_current_tts_engine()
        app = App.get_running_app()

        # Update the selected voice in the appropriate API's settings
        if current_engine == "ElevenLabs":
            app.api_elevenlabs.set_voice(voice_name)
        elif current_engine == "OpenAI":
            app.api_openai.set_voice(voice_name)
        elif current_engine == "Amazon Polly":
            app.api_amazonpolly.set_voice(voice_name)
        elif current_engine == "Microsoft Azure":
            app.api_msazure.set_voice(voice_name)

        # Update displayed selected voice
        self.selected_voice = voice_name
        self.voice_dropdown_menu.dismiss()

    def on_synthesize(self):
        current_engine = self.get_current_tts_engine()

        # Check the selected engine and call the respective synthesis method
        if current_engine == "ElevenLabs":
            self.on_synthesize_elevenlabs()
        elif current_engine == "OpenAI":
            self.on_synthesize_openai()
        elif current_engine == "Amazon Polly":
            self.on_synthesize_amazonpolly()
        elif current_engine == "Microsoft Azure":
            self.on_synthesize_msazure()
        else:
            log.error("No valid TTS engine selected.")

    def on_synthesize_elevenlabs(self):
        # TODO Implement text to speech synthesis (this is mostly a placeholder without a backend implementation yet)
        api = App.get_running_app().api_elevenlabs
        tmp_dir = App.get_running_app().global_settings.get_tmp_dir()
        file_path = os.path.join(tmp_dir, 'output_file.wav')
        log.info(f"Using file_path={file_path}")

        if api:
            try:
                # FIXME: Use constant or configurable output path
                api.synthesize(self.ids.text_main.text, file_path)
            except NotImplementedError:
                msg = "Text to speech synthesis not implemented for this API."
                log.error("%s: %s", self.__class__.__name__, msg)
                self.ids.label_status.text = msg
            except Exception as e:
                msg = "Error during synthesis"
                log.error("%s: %s: %s", self.__class__.__name__, msg, e)
                self.ids.label_status.text = msg
        popup_window = CustomPopup(content_text=f"Text has been synthesized\nto an audio file",
                                   size_hint=(None, None), size=(400, 400))
        popup_window.open()

    def on_synthesize_openai(self):
        api = App.get_running_app().api_openai
        tmp_dir = App.get_running_app().global_settings.get_tmp_dir()
        file_path = os.path.join(tmp_dir, 'openai_output.mp3')
        log.info(f"Using file_path={file_path}")

        if api:
            try:
                api.synthesize(self.ids.text_main.text, file_path)
            except Exception as e:
                msg = "Error during synthesis"
                log.error("%s: %s: %s", self.__class__.__name__, msg, e)
                self.ids.label_status.text = msg
        popup_window = CustomPopup(content_text="Text synthesized to an audio file.",
                                   size_hint=(None, None), size=(400, 400))
        popup_window.open()

    def on_synthesize_amazonpolly(self):
        api = App.get_running_app().api_amazonpolly
        tmp_dir = App.get_running_app().global_settings.get_tmp_dir()
        file_path = os.path.join(tmp_dir, 'amazon_polly_output.mp3')
        log.info(f"Using file_path={file_path}")

        if api:
            try:
                # Check for SSML emojis and set text_type
                self.check_for_ssml_content()
                processed_text = self.amazon_emoji_to_ssml_tag(self.ids.text_main.text)

                # Pass text_type to the Amazon Polly API for synthesis
                api.synthesize(processed_text, file_path, text_type=self.text_type)
            except Exception as e:
                msg = "Error during synthesis"
                log.error("%s: %s: %s", self.__class__.__name__, msg, e)
                self.ids.label_status.text = msg
        popup_window = CustomPopup(content_text="Text synthesized to an audio file.",
                                   size_hint=(None, None), size=(400, 400))
        popup_window.open()

    def on_synthesize_msazure(self):
        api = App.get_running_app().api_msazure
        tmp_dir = App.get_running_app().global_settings.get_tmp_dir()
        file_path = os.path.join(tmp_dir, 'azure_output.wav')
        log.info(f"Using file_path={file_path}")

        if api:
            try:
                api.synthesize(self.ids.text_main.text, file_path, ssml_conversion_func=self.msazure_emoji_to_ssml_tag)
            except Exception as e:
                msg = "Error during synthesis"
                log.error("%s: %s: %s", self.__class__.__name__, msg, e)
                self.ids.label_status.text = msg
        popup_window = CustomPopup(content_text="Text synthesized to an audio file.",
                                   size_hint=(None, None), size=(400, 400))
        popup_window.open()

    def play(self, audio_dir):
        try:
            mixer.init()
            mixer.music.load(audio_dir)
            mixer.music.play()
            # wait for music to finish playing
            while mixer.music.get_busy():
                time.sleep(1)
            mixer.music.unload()
        except Exception as e:
            log.error("%s: Error playing audio: %s", self.__class__.__name__, e)

    def on_play(self):
        tmp_dir = App.get_running_app().global_settings.get_tmp_dir()
        current_engine = self.get_current_tts_engine()

        # Check the selected engine and call the respective play function
        if current_engine == "ElevenLabs":
            audio_dir = os.path.join(tmp_dir, 'elevenlab_output.wav')
        elif current_engine == "OpenAI":
            audio_dir = os.path.join(tmp_dir, 'openai_output.mp3')
        elif current_engine == "Amazon Polly":
            audio_dir = os.path.join(tmp_dir, 'amazon_polly_output.mp3')
        elif current_engine == "Microsoft Azure":
            audio_dir = os.path.join(tmp_dir, 'msazure_output.mp3')
        else:
            log.error("No valid TTS engine selected.")

        if os.path.exists(audio_dir):
            self.play(audio_dir)
        else:
            self.ids.label_status.text = "Synthesized audio not found."

    def on_cursor_control(self):
        new_cursor_index = self.ids.text_main.cursor_index()
        old_cursor_index = self.old_cursor_index
        cnt_button = self.cnt_button
        old_cnt_button = self.old_cnt_button

        if abs(cnt_button - old_cnt_button) == 0 and abs(new_cursor_index - old_cursor_index) > 1:
            # set cursor to the end of the word
            cursor_in_row_index = self.ids.text_main._cursor[0]
            row = self.ids.text_main._cursor[1]
            text_row = self.ids.text_main._lines[row]

            spaces = []
            for index in range(cursor_in_row_index, len(text_row)):
                char = text_row[index]
                if char == " ":
                    spaces.append(index)
            if spaces:
                end_word_index = spaces[0]
                self.ids.text_main.cursor = (end_word_index, row)
            else:
                self.ids.text_main.do_cursor_movement('cursor_end')

        self.new_cursor_index = self.ids.text_main.cursor_index()
        self.save_old_cursor_index(new_cursor_index)
        self.save_old_cnt_button(cnt_button)

    def save_old_cursor_index(self, cursor_index):
        self.old_cursor_index = cursor_index

    def save_old_cnt_button(self, cnt_button):
        self.old_cnt_button = cnt_button

    def on_cursor_left(self):
        self.ids.text_main.do_cursor_movement('cursor_left')
        self.cnt_button = self.cnt_button + 1
        Clock.schedule_once(self.set_focus, 0.1)

    def on_cursor_right(self):
        self.ids.text_main.do_cursor_movement('cursor_right')
        self.cnt_button = self.cnt_button + 1
        Clock.schedule_once(self.set_focus, 0.1)

    def set_focus(self, dt):
        self.ids.text_main.focus = True


class CustomPopup(Popup):
    content_text = StringProperty("")

    def __init__(self, **kwargs):
        super(CustomPopup, self).__init__(**kwargs)


class Popups(FloatLayout):
    voice_name = StringProperty("")

    def __init__(self, voice_name="", **kwargs):
        super(Popups, self).__init__(**kwargs)
        self.voice_name = voice_name
