import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile, os

model = whisper.load_model("base")  # or "small" for better accuracy

def listen():
    print("Listening...")
    duration = 5  # seconds
    fs = 16000
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav.write(f.name, fs, audio)
        result = model.transcribe(f.name)
        os.unlink(f.name)
    
    return result["text"].strip()