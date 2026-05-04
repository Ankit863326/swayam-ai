import json, os
from datetime import datetime

MEMORY_FILE = os.path.join("Data", "memory.json")

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"conversations": []}

def save_memory(memory):
    os.makedirs("Data", exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)

def add_conversation(user_msg, ai_msg):
    memory = load_memory()
    memory["conversations"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "user": user_msg,
        "ai"  : ai_msg
    })
    memory["conversations"] = memory["conversations"][-100:]
    save_memory(memory)

def get_context(n=10):
    memory = load_memory()
    recent = memory["conversations"][-n:]
    context = ""
    for c in recent:
        context += f"User: {c['user']}\nSwayam: {c['ai']}\n"
    return context