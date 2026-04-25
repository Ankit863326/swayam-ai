import os
import sys
import json
import threading
import subprocess
from asyncio import run
from time import sleep
from dotenv import dotenv_values

print("1. Starting imports...")

# --- 1. Import GUI Elements ---
print("2. Importing GUI...")
from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)

# --- 2. Import Backend Modules ---
print("3. Importing Backend Model...")
from Backend.Model import FirstLayerDMM

print("4. Importing Search Engine...")
from Backend.RealtimeSearchEngine import RealtimeSearchEngine

print("5. Importing Automation...")
from Backend.Automation import Automation

# In your Main.py, ensure line 6 imports the function correctly:
print("6. Importing SpeechToText (Dual Mode)...")
from Backend.SpeechToText import listen_fast as SpeechRecognition

print("7. Importing ChatBot...")
from Backend.Chatbot import ChatBot

print("8. Importing TextToSpeech (EdgeTTS + MPV)...")
from Backend.TextToSpeech import TextToSpeech

# --- 3. Configuration ---
print("9. Loading .env variables...")
# Ensure this path is correct for your PC
env_path = r"C:\Users\amits\OneDrive\Documents\Desktop\Swayambhu  A.I\.env"

print(f"9.1 Checking env path: {env_path}")
if not os.path.exists(env_path):
    print("WARNING: .env file not found at path! proceeding with defaults.")

try:
    env_vars = dotenv_values(env_path)
    print("9.2 Env loaded successfully.")
except Exception as e:
    print(f"9.2 Error loading env: {e}")
    env_vars = {}

Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Swayam")

DefaultMessage = f"""{Username} : Hello {Assistantname}! How are you?
{Assistantname} : Hello {Username}, I'm doing well. How can I help you today?
"""

subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

# --- 4. Setup Functions ---
def ShowDefaultChatIfNoChats():
    chat_log_path = r"Data\ChatLog.json"
    os.makedirs("Data", exist_ok=True)
    if not os.path.exists(chat_log_path) or os.path.getsize(chat_log_path) < 5:
        with open(chat_log_path, "w", encoding="utf-8") as file:
            json.dump([], file)
    
    # Ensure Frontend/Files exists before writing!
    os.makedirs(os.path.join("Frontend", "Files"), exist_ok=True)
    
    with open(TempDirectoryPath("Database.data"), "w", encoding="utf-8") as file:
        file.write("")
    with open(TempDirectoryPath("Responses.data"), "w", encoding="utf-8") as file:
        file.write(DefaultMessage)

def ReadChatLogJson():
    chat_log_path = r"Data\ChatLog.json"
    if os.path.exists(chat_log_path):
        with open(chat_log_path, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    if json_data:
        formatted_chatlog = "\n".join(
            f"{Username if entry['role'] == 'user' else Assistantname} : {entry['content']}"
            for entry in json_data
        )
    
    os.makedirs(os.path.join("Frontend", "Files"), exist_ok=True)
    with open(TempDirectoryPath("Database.data"), "w", encoding="utf-8") as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    db_path = TempDirectoryPath("Database.data")
    response_path = TempDirectoryPath("Responses.data")
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as file:
            data = file.read()
        if data:
            os.makedirs(os.path.join("Frontend", "Files"), exist_ok=True)
            with open(response_path, "w", encoding="utf-8") as file:
                file.write(data)

def InitialExecution():
    print("10. Running Initial Execution...")
    
    # CRITICAL FIX: Create directory before SetMicrophoneStatus tries to write
    print("10.1 Creating Temp Folders...")
    os.makedirs(os.path.join("Frontend", "Files"), exist_ok=True)
    os.makedirs("Data", exist_ok=True)
    
    print("10.2 Setting Microphone Status...")
    SetMicrophoneStatus("False")
    
    print("10.3 Setting Assistant Status...")
    ShowTextToScreen("")
    
    print("10.4 initializing Chat Logs...")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()
    
    print("11. Initial Execution Done.")

# Run setup once
InitialExecution()

# --- 5. Main Execution Logic ---
def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    # 1. LISTEN
    SetAssistantStatus("Listening...")
    try:
        # This calls 'listen_fast()' from your STT file
        Query = SpeechRecognition()
        
        if not Query: 
            return 
            
    except Exception as e:
        print(f"Mic Error: {e}")
        return

    # 2. SHOW INPUT
    ShowTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Thinking...")

    # 3. DECIDE (AI Brain)
    try:
        Decision = FirstLayerDMM(Query)
    except Exception as e:
        print(f"Decision Error: {e}")
        return

    print(f"\nDecision: {Decision}\n")

    # 4. PROCESS DECISION
    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)

    Merged_query = " and ".join(
        i.split(maxsplit=1)[1] for i in Decision 
        if i.startswith(("general", "realtime")) and len(i.split(maxsplit=1)) > 1
    )

    # Check for Image Gen
    for queries in Decision:
        if queries.startswith("generate "):
            ImageGenerationQuery = queries
            ImageExecution = True

    # Check for Automation Tasks
    for queries in Decision:
        if not TaskExecution and any(queries.startswith(func) for func in Functions):
            run(Automation(list(Decision)))
            TaskExecution = True

    # Handle Image Gen Execution
    if ImageExecution:
        with open(TempDirectoryPath("ImageGeneration.data"), "w", encoding="utf-8") as file:
            file.write(f"{ImageGenerationQuery},True")
        try:
            p1 = subprocess.Popen(["python", r"Backend\ImageGeneration.py"], shell=False)
            subprocesses.append(p1)
        except Exception as e:
            print(f"Error Generating Image: {e}")

    # 5. GENERATE RESPONSE & SPEAK
    if G and R or R:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
        ShowTextToScreen(f"{Assistantname} : {Answer}")
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
        return True

    for Queries in Decision:
        if Queries.startswith("general "):
            SetAssistantStatus("Thinking...")
            Answer = ChatBot(QueryModifier(Queries.replace("general ", "")))
            ShowTextToScreen(f"{Assistantname} : {Answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(Answer)
            return True

        elif Queries.startswith("realtime "):
            SetAssistantStatus("Thinking...")
            Answer = RealtimeSearchEngine(QueryModifier(Queries.replace("realtime ", "")))
            ShowTextToScreen(f"{Assistantname} : {Answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(Answer)
            return True

        elif Queries == "exit":
            ShowTextToScreen(f"{Assistantname} : Okay, Bye!")
            SetAssistantStatus("Answering...")
            TextToSpeech("Okay, Bye!")
            os._exit(1)

# --- 6. Threading (GUI + Logic) ---
def FirstThread(): 
    print("Listening Thread Started...")
    while True:
        status = GetMicrophoneStatus()
        if status == "True":
            MainExecution()
        else:
            if GetAssistantStatus() != "Available...":
                SetAssistantStatus("Available...")
            sleep(0.1)

def SecondThread():
    print("12. Launching GUI...")
    GraphicalUserInterface()

if __name__ == "__main__":
    print("Starting Threads...")
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()