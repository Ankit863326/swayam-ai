import datetime
import os
from json import dump, load
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

Username = os.getenv("Username")
Assistantname = os.getenv("Assistantname")
GroqAPIKey = os.getenv("GroqAPIKey")

client = Groq(api_key=GroqAPIKey)

messages: list = []

System = f"""Hello, I am {Username}. You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

SystemChatBot = [
    {"role": "system", "content": System},
]

# Ensure Data folder exists
try:
    with open(r"Data\ChatLog.json", "r") as file:
        messages = load(file)
except FileNotFoundError:
    # Make sure to handle the case where the Data directory might not exist
    import os
    os.makedirs("Data", exist_ok=True) 
    with open(r"Data\ChatLog.json", "w") as file:
        dump([], file, indent=4)

def RealtimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data = "Please use this real-time information if needed,\n"
    data += f"Day: {day}\nDate: {date} {month} {year}\nTime: {hour}:{minute}:{second}"
    return data

def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip() != ""]
    modified_answer = "\n".join(non_empty_lines)
    return modified_answer

def ChatBot(Query):
    try:
        # Load history
        with open(r"Data\ChatLog.json", "r") as file:
            messages = load(file)

        messages.append({"role": "user", "content": Query})

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", # This model is active and fast
            messages=SystemChatBot
            + [{"role": "system", "content": RealtimeInformation()}]
            + messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=False,
            stop=None,
        )

        Answer = completion.choices[0].message.content
        Answer = Answer.replace("</s>", "")

        messages.append({"role": "assistant", "content": Answer})

        # Save history
        with open(r"Data\ChatLog.json", "w") as file:
            dump(messages, file, indent=4)

        return AnswerModifier(Answer)

    except Exception as e:
        # 3. FIX: Print the error and STOP. Do not call ChatBot() again.
        print(f"Error: {e}")
        # Reset log if corrupted
        with open(r"Data\ChatLog.json", "w") as file:
            dump([], file, indent=4)
        return "I encountered an error and could not process your request."

if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        # Add an exit command
        if user_input.lower() in ["exit", "bye", "quit"]:
            break
        print(ChatBot(user_input))