import sys
import asyncio
from webbrowser import open as webopen
from dotenv import load_dotenv

load_dotenv()


# ── System controls ───────────────────────────────────────────
def System(command: str) -> bool:
    command = command.strip().lower()
    if sys.platform == "win32":
        try:
            import keyboard
            actions = {
                "mute":        "volume mute",
                "unmute":      "volume mute",
                "volume up":   "volume up",
                "volume down": "volume down",
            }
            if command in actions:
                keyboard.press_and_release(actions[command])
        except Exception as e:
            print(f"[System Error] {e}")
    else:
        # Linux/Mac: use amixer or applescript
        if command in ("mute", "unmute"):
            os.system("amixer set Master toggle 2>/dev/null")
        elif command == "volume up":
            os.system("amixer set Master 5%+ 2>/dev/null")
        elif command == "volume down":
            os.system("amixer set Master 5%- 2>/dev/null")
    return True


# ── App open / close ─────────────────────────────────────────
def OpenApp(app_name: str) -> bool:
    try:
        from AppOpener import open as appopen
        appopen(app_name, match_closest=True, output=True, throw_error=True)
        return True
    except Exception:
        # fallback to Google
        webopen(f"https://www.google.com/search?q={app_name}")
        return True


def CloseApp(app_name: str) -> bool:
    try:
        from AppOpener import close
        close(app_name, match_closest=True, output=True, throw_error=True)
        return True
    except Exception:
        return False


# ── Web & media ───────────────────────────────────────────────
def PlayYoutube(query: str) -> bool:
    try:
        import pywhatkit
        pywhatkit.playonyt(query)
    except Exception as e:
        print(f"[YouTube Error] {e}")
        webopen(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
    return True


def YouTubeSearch(topic: str) -> bool:
    webopen(f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}")
    return True


def GoogleSearch(topic: str) -> bool:
    webopen(f"https://www.google.com/search?q={topic.replace(' ', '+')}")
    return True


# ── Content (open text file) ──────────────────────────────────
def Content(topic: str) -> bool:
    topic = topic.replace("Content ", "").strip()
    filepath = os.path.join("Data", f"{topic.lower().replace(' ', '_')}.txt")
    os.makedirs("Data", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"AI Generated Content for: {topic}\n")

    # cross-platform open
    if sys.platform == "win32":
        os.startfile(filepath)
    elif sys.platform == "darwin":
        os.system(f"open '{filepath}'")
    else:
        os.system(f"xdg-open '{filepath}'")
    return True


# ── Dispatcher ────────────────────────────────────────────────
async def TranslateAndExecute(commands: list[str]):
    tasks = []
    for cmd in commands:
        cmd = cmd.lower().strip()
        if cmd.startswith("open "):
            tasks.append(asyncio.to_thread(OpenApp,       cmd.removeprefix("open ").strip()))
        elif cmd.startswith("close "):
            tasks.append(asyncio.to_thread(CloseApp,      cmd.removeprefix("close ").strip()))
        elif cmd.startswith("play "):
            tasks.append(asyncio.to_thread(PlayYoutube,   cmd.removeprefix("play ").strip()))
        elif cmd.startswith("content "):
            tasks.append(asyncio.to_thread(Content,       cmd.removeprefix("content ").strip()))
        elif cmd.startswith("google search "):
            tasks.append(asyncio.to_thread(GoogleSearch,  cmd.removeprefix("google search ").strip()))
        elif cmd.startswith("youtube search "):
            tasks.append(asyncio.to_thread(YouTubeSearch, cmd.removeprefix("youtube search ").strip()))
        elif cmd.startswith("system "):
            tasks.append(asyncio.to_thread(System,        cmd.removeprefix("system ").strip()))
    if tasks:
        await asyncio.gather(*tasks)


def Automation(commands):
    if isinstance(commands, str):
        commands = [commands]
    asyncio.run(TranslateAndExecute(commands))
    return True