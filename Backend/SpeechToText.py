import pyaudio
import json
import os
import sys
from vosk import Model, KaldiRecognizer

# Function to automatically find model folders
def find_model_path(keywords):
    """
    Searches the current directory for a folder containing 'conf' (a key Vosk file)
    and matches the keywords (like 'en' or 'hi') to guess the language.
    """
    current_dir = os.getcwd()
    print(f"Searching for {keywords} model in {current_dir}...")
    
    for root, dirs, files in os.walk(current_dir):
        # We are looking for a folder that contains the file 'mfcc.conf' or a folder named 'conf'
        if 'conf' in dirs or 'model.conf' in files:
            # This looks like a valid model folder!
            # Check if the path has our keywords (e.g., 'en-in', 'hi')
            if any(k in root.lower() for k in keywords):
                return root
                
    return None

def load_models():
    print("------------------------------------------------")
    print("Auto-Detecting Models...")
    
    models = {}
    
    # 1. Find English Model (looks for 'en' or 'indian')
    en_path = find_model_path(["en-in", "en-us", "model_en"])
    if en_path:
        print(f"✅ Found English Model at: {en_path}")
        models['en'] = Model(en_path)
    else:
        print("❌ Could not find an English model folder automatically.")

    # 2. Find Hindi Model (looks for 'hi' or 'hindi')
    hi_path = find_model_path(["hi", "hindi", "model_hi"])
    if hi_path:
        print(f"✅ Found Hindi Model at: {hi_path}")
        models['hi'] = Model(hi_path)
    else:
        print("⚠️ Could not find a Hindi model folder (Skipping Hindi).")
        
    if not models:
        print("\nCRITICAL ERROR: No Vosk models found in your folder!")
        print("Please ensure you unzipped the downloaded model files inside 'Swayambhu A.I'")
        sys.exit(1)
        
    print("Models Loaded Successfully!")
    return models

# Load models ONCE
models = load_models()

def listen_fast():
    # Create Recognizers
    recognizers = []
    if 'en' in models:
        recognizers.append(KaldiRecognizer(models['en'], 16000))
    if 'hi' in models:
        recognizers.append(KaldiRecognizer(models['hi'], 16000))

    if not recognizers:
        return ""

    # Setup Mic
    mic = pyaudio.PyAudio()
    # Auto-select best input device if possible, otherwise default
    try:
        stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
    except:
        # Fallback for some windows systems
        stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, input_device_index=1, frames_per_buffer=8192)

    stream.start_stream()
    print("Listening...")

    while True:
        try:
            data = stream.read(4096, exception_on_overflow=False)
            
            for rec in recognizers:
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    
                    if text:
                        print(f"User: {text}")
                        stream.stop_stream()
                        stream.close()
                        mic.terminate()
                        return text

        except Exception as e:
            # print(f"Error: {e}") # clean logs
            break