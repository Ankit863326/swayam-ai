import os
import asyncio
import keyboard # pip install keyboard
from webbrowser import open as webopen
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

# --- 1. System Functions (Fast & Offline) ---
def OpenNotepad(filename):
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("")
    os.startfile(filename)

def System(command):
    command = command.strip().lower()
    if command == "mute":
        keyboard.press_and_release("volume mute")
    elif command == "unmute":
        keyboard.press_and_release("volume mute")
    elif command == "volume up":
        keyboard.press_and_release("volume up")
    elif command == "volume down":
        keyboard.press_and_release("volume down")
    return True

# --- 2. App Management (Safe Imports) ---
def OpenApp(app_name):
    try:
        # Import AppOpener only when needed to save startup time
        from AppOpener import open as appopen
        appopen(app_name, match_closest=True, output=True, throw_error=True)
        return True
    except:
        # Fallback to Google Search if app not found
        webopen(f"https://www.google.com/search?q={app_name}")
        return True

def CloseApp(app_name):
    try:
        from AppOpener import close
        close(app_name, match_closest=True, output=True, throw_error=True)
        return True
    except:
        return False

# --- 3. Web & Content Functions ---
def PlayYoutube(query):
    try:
        # Import pywhatkit only when needed to prevent startup crashes
        import pywhatkit
        pywhatkit.playonyt(query)
    except Exception as e:
        print(f"Internet Error: {e}")
        webopen(f"https://www.youtube.com/results?search_query={query}")
    return True

def Content(Topic):
    Topic = str(Topic).replace("Content ", "")
    filepath = rf"Data\{Topic.lower().replace(' ', '_')}.txt"
    os.makedirs("Data", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(f" AI Generated Content for: {Topic}")
    OpenNotepad(filepath)
    return True

def YouTubeSearch(Topic):
    webopen(f"https://www.youtube.com/results?search_query={Topic}")
    return True

def GoogleSearch(Topic):
    webopen(f"https://www.google.com/search?q={Topic}")
    return True

# --- 4. Main Execution Logic ---
async def TranslateAndExecute(commands: list[str]):
    funcs = []
    for command in commands:
        command = command.lower()
        if command.startswith("open "):
            app_name = command.removeprefix("open ").strip()
            fun = asyncio.to_thread(OpenApp, app_name)
            funcs.append(fun)
        elif command.startswith("play "):
            query = command.removeprefix("play ").strip()
            fun = asyncio.to_thread(PlayYoutube, query)
            funcs.append(fun)
        elif command.startswith("content "):
            topic = command.removeprefix("content ").strip()
            fun = asyncio.to_thread(Content, topic)
            funcs.append(fun)
        elif command.startswith("google search "):
            query = command.removeprefix("google search ").strip()
            fun = asyncio.to_thread(GoogleSearch, query)
            funcs.append(fun)
        elif command.startswith("youtube search "):
            query = command.removeprefix("youtube search ").strip()
            fun = asyncio.to_thread(YouTubeSearch, query)
            funcs.append(fun)
        elif command.startswith("system "):
            cmd = command.removeprefix("system ").strip()
            fun = asyncio.to_thread(System, cmd)
            funcs.append(fun)
            
    if funcs:
        await asyncio.gather(*funcs)

def Automation(commands):
    if isinstance(commands, list):
        asyncio.run(TranslateAndExecute(commands))
    elif isinstance(commands, str):
        asyncio.run(TranslateAndExecute([commands]))
    return True