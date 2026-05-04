import os
import sys
import json
import threading
import subprocess
from asyncio import run
from time import sleep
from dotenv import load_dotenv

# ── Load .env ─────────────────────────────────────────────────
load_dotenv()

# ── Import GUI ────────────────────────────────────────────────
from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus,
)

# ── Import Backend ────────────────────────────────────────────
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation           import Automation
from Backend.SpeechToText         import listen as SpeechRecognitionon
from Backend.Chatbot              import ChatBot
from Backend.TextToSpeech         import TextToSpeech
from Backend.WakeWord             import wait_for_wake_word        # NEW
from Backend.Memory               import add_conversation, get_context  # NEW

# ── Config ────────────────────────────────────────────────────
Username      = os.getenv("Username",      "User")
AssistantName = os.getenv("Assistantname", "Swayam")

CHAT_LOG = os.path.join("Data", "ChatLog.json")

DefaultMessage = (
    f"{Username} : Hello {AssistantName}! How are you?\n"
    f"{AssistantName} : Hello {Username}, I am doing well. How can I help you today?\n"
)

subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]


# ── Setup helpers ─────────────────────────────────────────────
def ShowDefaultChatIfNoChats():
    os.makedirs("Data", exist_ok=True)
    os.makedirs(os.path.join("Frontend", "Files"), exist_ok=True)
    if not os.path.exists(CHAT_LOG) or os.path.getsize(CHAT_LOG) < 5:
        with open(CHAT_LOG, "w", encoding="utf-8") as f:
            json.dump([], f)
    open(TempDirectoryPath("Database.data"),  "w", encoding="utf-8").write("")
    open(TempDirectoryPath("Responses.data"), "w", encoding="utf-8").write(DefaultMessage)
    open(TempDirectoryPath("TextInput.data"), "w", encoding="utf-8").write("")


def ReadChatLogJson():
    if os.path.exists(CHAT_LOG):
        try:
            with open(CHAT_LOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def ChatLogIntegration():
    data = ReadChatLogJson()
    lines = ""
    if data:
        lines = "\n".join(
            f"{Username if e['role']=='user' else AssistantName} : {e['content']}"
            for e in data
        )
    os.makedirs(os.path.join("Frontend", "Files"), exist_ok=True)
    open(TempDirectoryPath("Database.data"), "w", encoding="utf-8").write(AnswerModifier(lines))


def ShowChatsOnGUI():
    db = TempDirectoryPath("Database.data")
    if os.path.exists(db):
        content = open(db, "r", encoding="utf-8").read()
        if content:
            open(TempDirectoryPath("Responses.data"), "w", encoding="utf-8").write(content)


def InitialExecution():
    os.makedirs(os.path.join("Frontend", "Files"), exist_ok=True)
    os.makedirs("Data", exist_ok=True)
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()
    print(f"[{AssistantName}] Ready.")


# ── Main loop ─────────────────────────────────────────────────
def MainExecution():
    TaskExecution        = False
    ImageExecution       = False
    ImageGenerationQuery = ""

    # ── 1. Check typed input from GUI ─────────────────────
    text_input_path = TempDirectoryPath("TextInput.data")
    typed_query = ""
    if os.path.exists(text_input_path):
        typed_query = open(text_input_path, "r", encoding="utf-8").read().strip()
        if typed_query:
            open(text_input_path, "w", encoding="utf-8").write("")

    # ── 2. Mic input if no typed input ────────────────────
    if typed_query:
        Query = typed_query
        print(f"[TextInput] {Query}")
    else:
        mic_status = GetMicrophoneStatus()
        if mic_status != "True":
            return
        SetAssistantStatus("Listening...")
        try:
            Query = SpeechRecognition()
            if not Query:
                return
        except Exception as e:
            print(f"[Mic Error] {e}")
            return

    # ── 3. Show input, decide ─────────────────────────────
    ShowTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Thinking...")

    try:
        from Backend.Model import FirstLayerDMM
        Decision = FirstLayerDMM(Query)
    except Exception as e:
        print(f"[Decision Error] {e}")
        Decision = [f"general {Query}"]

    print(f"[Decision] {Decision}")

    # ── 4. Process flags ──────────────────────────────────
    G = any(i.startswith("general")  for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)

    Merged_query = " and ".join(
        i.split(maxsplit=1)[1] for i in Decision
        if i.startswith(("general", "realtime")) and len(i.split(maxsplit=1)) > 1
    )

    for q in Decision:
        if q.startswith("generate "):
            ImageGenerationQuery = q
            ImageExecution = True

    for q in Decision:
        if not TaskExecution and any(q.startswith(fn) for fn in Functions):
            run(Automation(list(Decision)))
            TaskExecution = True

    if ImageExecution:
        with open(TempDirectoryPath("ImageGeneration.data"), "w", encoding="utf-8") as f:
            f.write(f"{ImageGenerationQuery},True")
        try:
            p = subprocess.Popen(
                [sys.executable, os.path.join("Backend", "ImageGeneration.py")],
                shell=False
            )
            subprocesses.append(p)
        except Exception as e:
            print(f"[ImageGen Error] {e}")

    # ── 5. Generate answer ────────────────────────────────
    if G and R or R:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
        ShowTextToScreen(f"{AssistantName} : {Answer}")
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
        add_conversation(Query, Answer)   # MEMORY SAVE
        return

    for q in Decision:
        if q.startswith("general "):
            SetAssistantStatus("Thinking...")
            Answer = ChatBot(QueryModifier(q.replace("general ", "", 1)))
            ShowTextToScreen(f"{AssistantName} : {Answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(Answer)
            add_conversation(Query, Answer)   # MEMORY SAVE
            return

        elif q.startswith("realtime "):
            SetAssistantStatus("Searching...")
            Answer = RealtimeSearchEngine(QueryModifier(q.replace("realtime ", "", 1)))
            ShowTextToScreen(f"{AssistantName} : {Answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(Answer)
            add_conversation(Query, Answer)   # MEMORY SAVE
            return

        elif q.strip() == "exit":
            ShowTextToScreen(f"{AssistantName} : Goodbye, {Username}!")
            SetAssistantStatus("Answering...")
            TextToSpeech(f"Goodbye, {Username}!")
            sleep(2)
            os._exit(0)


# ── Threads ───────────────────────────────────────────────────
def ListeningThread():
    print("[Thread] Listening loop started.")
    while True:
        try:
            wait_for_wake_word()   # WAKE WORD — waits for "Swayam"
            MainExecution()
        except Exception as e:
            print(f"[MainExecution Error] {e}")
        sleep(0.05)


def GUIThread():
    print("[Thread] GUI starting.")
    GraphicalUserInterface()


# ── Entry ─────────────────────────────────────────────────────
if __name__ == "__main__":
    InitialExecution()

    backend_thread = threading.Thread(target=ListeningThread, daemon=True)
    backend_thread.start()

    GUIThread()