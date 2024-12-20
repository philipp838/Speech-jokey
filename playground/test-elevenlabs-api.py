try:
    from elevenlabs import stream, save
    from elevenlabs.client import ElevenLabs
except ImportError:
    raise ImportError(
        "Please install elevenlabs module: pip install elevenlabs (for installation details: https://github.com/elevenlabs/elevenlabs-python)")

elevenlabs_ref=ElevenLabs(api_key="sk_ab8fc6ea8dc84745bef3abc323403043cb030cd04513b52c")
voices=elevenlabs_ref.voices.get_all().voices
#print(voices)

#voices = ['Alex', 'Alice', 'Alva', 'Amelie', 'Anna', 'Carmit', 'Damayanti', 'Daniel', 'Diego', 'Ellen', 'Fiona', 'Fred', 'Ioana', 'Joana', 'Jorge', 'Juan', 'Kanya', 'Karen', 'Kyoko', 'Laura', 'Lekha', 'Luca', 'Luciana', 'Maged', 'Mariska', 'Mei-Jia', 'Melina', 'Milena', 'Moira', 'Monica', 'Nora', 'Paulina', 'Samantha', 'Sara', 'Satu', 'Sin-ji', 'Tessa', 'Thomas', 'Ting-Ting', 'Tom', 'Veena', 'Victoria', 'Xander', 'Yelda', 'Yuna', 'Yuri', 'Zosia', 'Zuzana']
for voice in voices:
    print(voice)

voices_names=[voice.name for voice in voices]
print(voices_names)

models=elevenlabs_ref.models.get_all()
model_names=[model.name for model in models if model.can_do_text_to_speech]
print(model_names)