import asyncio
import os
import sys
import random
import subprocess
from dotenv import load_dotenv

load_dotenv()

AssistantVoice = os.getenv("AssistantVoice", "en-US-GuyNeural")
AUDIO_FILE = os.path.join("Frontend", "Files", "response_audio.mp3")

_SHORT_RESPONSES = [
    "I have shown the rest on screen.",
    "Check the screen for the full details.",
    "The complete answer is on your screen.",
]


async def _generate_audio(text: str) -> bool:
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, AssistantVoice, pitch="+0Hz", rate="+5%")
        os.makedirs(os.path.dirname(AUDIO_FILE), exist_ok=True)
        await communicate.save(AUDIO_FILE)
        return True
    except Exception as e:
        print(f"[TTS Generate Error] {e}")
        return False


def _play_audio(filepath: str):
    if not os.path.exists(filepath):
        return

    if sys.platform == "win32":
        try:
            import winsound
            winsound.PlaySound(filepath, winsound.SND_FILENAME)
        except Exception:
            subprocess.call(
                ["powershell", "-c",
                 f"(New-Object Media.SoundPlayer '{filepath}').PlaySync()"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    elif sys.platform == "darwin":
        subprocess.call(["afplay", filepath],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        players = [
            ["mpv", "--no-terminal", filepath],
            ["cvlc", "--play-and-exit", "--quiet", filepath],
            ["aplay", filepath],
        ]
        for cmd in players:
            try:
                subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except FileNotFoundError:
                continue
        print("[TTS] No audio player found. Install mpv: sudo apt install mpv")


def TTS(text: str):
    text = text.strip()
    if not text:
        return
    success = asyncio.run(_generate_audio(text))
    if success:
        _play_audio(AUDIO_FILE)


def TextToSpeech(text: str):
    text = str(text).strip()
    if not text:
        return
    sentences = text.split(".")
    if len(sentences) > 6 and len(text) >= 300:
        spoken = ". ".join(sentences[:2]).strip() + ". " + random.choice(_SHORT_RESPONSES)
    else:
        spoken = text
    TTS(spoken)


if __name__ == "__main__":
    test = "Hello! I am Swayam, your personal AI assistant. How may I help you today?"
    print(f"Testing TTS with voice: {AssistantVoice}")
    TextToSpeech(test)