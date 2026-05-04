import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import os

# Load once at startup — use "small" for better accuracy
model = whisper.load_model("base")

def listen():
    print("🎤 Listening...")
    duration = 5   # seconds to record
    fs = 16000

    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    # Save to temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav.write(tmp.name, fs, audio)

    # Transcribe
    result = model.transcribe(tmp.name, language="en")
    os.unlink(tmp.name)

    text = result["text"].strip()
    print(f"[STT] You said: {text}")
    return text

# Alias so both names work
listen_fast = listen