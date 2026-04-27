# ============================================================
#  Backend/Chatbot.py  —  Swayam AI
#  FIXED: cross-platform paths, memory limit, better model
# ============================================================

import datetime
import os
from json import dump, load
from dotenv import load_dotenv
from groq import Groq

# ── Config ───────────────────────────────────────────────────
load_dotenv()

Username      = os.getenv("Username",      "User")
AssistantName = os.getenv("Assistantname", "Swayam")
GroqAPIKey    = os.getenv("GroqAPIKey",    "")

client = Groq(api_key=GroqAPIKey)

CHAT_LOG    = os.path.join("Data", "ChatLog.json")
MAX_HISTORY = 20   # keep last 20 messages to avoid context overflow

# ── System prompt (Jarvis personality) ───────────────────────
System = f"""You are {AssistantName}, a highly advanced AI personal assistant for {Username}.
You are inspired by J.A.R.V.I.S. — intelligent, precise, slightly witty, and always professional.

PERSONALITY RULES:
- Address the user as "{Username}" occasionally to feel personal.
- Be concise. Do not write long paragraphs unless the user specifically asks for details.
- Use a confident, calm tone. Avoid filler phrases like "Sure!", "Of course!", "Great question!".
- For lists, use clean numbered format.
- Never say "As an AI language model..." or mention your training data.
- If asked about yourself, say you are {AssistantName}, a personal AI assistant created for {Username}.
- Occasionally be slightly witty — one clever remark is better than none.

FORMATTING:
- Keep answers under 3 sentences for simple factual questions.
- For multi-step answers, use numbered steps.
- Do NOT add disclaimers or unnecessary notes.

LANGUAGE: Always respond in English only.
Real-time date/time will be provided in context.
"""

SystemChatBot = [{"role": "system", "content": System}]

# ── Ensure Data folder + log file exist ──────────────────────
os.makedirs("Data", exist_ok=True)
if not os.path.exists(CHAT_LOG):
    with open(CHAT_LOG, "w", encoding="utf-8") as f:
        dump([], f)


# ── Helpers ──────────────────────────────────────────────────
def RealtimeInformation():
    now = datetime.datetime.now()
    return (
        f"Current Date & Time: {now.strftime('%A, %d %B %Y  %H:%M:%S')}\n"
        f"Timezone: Local system time."
    )


def AnswerModifier(Answer):
    return "\n".join(l for l in Answer.split("\n") if l.strip())


# ── Main chatbot function ─────────────────────────────────────
def ChatBot(Query):
    try:
        # Load history
        with open(CHAT_LOG, "r", encoding="utf-8") as f:
            messages = load(f)

        # Trim to last MAX_HISTORY messages to avoid token overflow
        messages = messages[-MAX_HISTORY:]

        messages.append({"role": "user", "content": Query})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # smarter model
            messages=(
                SystemChatBot
                + [{"role": "system", "content": RealtimeInformation()}]
                + messages
            ),
            max_tokens=2048,
            temperature=0.65,
            top_p=1,
            stream=False,
            stop=None,
        )

        Answer = completion.choices[0].message.content
        Answer = Answer.replace("</s>", "").strip()

        messages.append({"role": "assistant", "content": Answer})

        # Save history (trimmed)
        with open(CHAT_LOG, "w", encoding="utf-8") as f:
            dump(messages, f, indent=4, ensure_ascii=False)

        return AnswerModifier(Answer)

    except Exception as e:
        print(f"[ChatBot Error] {e}")
        # Reset corrupted log
        with open(CHAT_LOG, "w", encoding="utf-8") as f:
            dump([], f)
        return "I encountered an error. Please try again."


# ── CLI test ─────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"{AssistantName} CLI — type 'exit' to quit\n")
    while True:
        user_input = input(f"{Username}: ").strip()
        if user_input.lower() in ["exit", "bye", "quit"]:
            break
        if user_input:
            print(f"{AssistantName}: {ChatBot(user_input)}\n")