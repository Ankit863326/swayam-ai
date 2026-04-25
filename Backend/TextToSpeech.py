import subprocess
import asyncio
import edge_tts
import os
import sys
import random
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values(".env")
# Fallback to a safe US voice if the .env one is wrong
AssistantVoice = env_vars.get("AssistantVoice", "en-US-AriaNeural")

async def stream_tts(text, func=lambda r=None: True) -> None:
    """
    Streams audio directly to mpv.
    """
    try:
        # Check if text is empty
        if not text or not text.strip():
            return

        communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+0Hz', rate='+0%')
        
        # Start mpv process
        mpv_process = subprocess.Popen(
            ["mpv", "--no-cache", "--no-terminal", "--", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        async for chunk in communicate.stream():
            if func() == False:
                mpv_process.kill()
                break

            if chunk["type"] == "audio":
                if mpv_process.stdin:
                    try:
                        mpv_process.stdin.write(chunk["data"])
                        mpv_process.stdin.flush()
                    except BrokenPipeError:
                        break
        
        if mpv_process.stdin:
            mpv_process.stdin.close()
        mpv_process.wait()

    except Exception as e:
        print(f"Error in TTS Streaming: {e}")
        # If the specific voice fails, don't crash, just print.
        # This keeps the GUI alive.

def TTS(Text, func=lambda r=None: True):
    try:
        asyncio.run(stream_tts(Text, func))
    except Exception as e:
        print(f"Error in TTS Wrapper: {e}")

def TextToSpeech(Text, func=lambda r=None: True):
    # This logic handles long text breaks
    Data = str(Text).split(".")
    
    # Generic responses for very long processing
    responses = [
        "Check the screen for the rest.",
        "I have printed the details mostly on the screen."
    ]

    if len(Data) > 6 and len(Text) >= 300:
        # Speak the first 2 sentences, then print the rest
        TTS(" ".join(Text.split(".")[0:2]) + "." + random.choice(responses), func)
    else:
        TTS(Text, func)

if __name__ == "__main__":
    TextToSpeech("Hello Ankit, this is a test of the Indian English voice.")