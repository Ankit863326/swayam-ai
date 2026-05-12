import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import os

# Load once at startup — use "base" for speed, "small" for better accuracy
try:
    model = whisper.load_model("base")
    print("[STT] Whisper model loaded.")
except Exception as e:
    print(f"[STT Error] Failed to load Whisper model: {e}")
    model = None

def listen():
    if model is None:
        print("[STT Error] Whisper model not loaded.")
        return ""

    print("🎤 Listening...")
    duration = 5   # seconds to record
    fs = 16000

    try:
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
    except Exception as e:
        print(f"[STT Error] Microphone recording failed: {e}")
        return ""

    # Save to temp file
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        wav.write(tmp.name, fs, audio)
    except Exception as e:
        print(f"[STT Error] Failed to save audio: {e}")
        return ""

    # Transcribe
    try:
        result = model.transcribe(tmp.name, language="en")
        os.unlink(tmp.name)
        text = result["text"].strip()
        print(f"[STT] You said: {text}")
        return text
    except Exception as e:
        print(f"[STT Error] Transcription failed: {e}")
        try:
            os.unlink(tmp.name)
        except:
            pass
        return ""

# Alias so both names work
listen_fast = listen