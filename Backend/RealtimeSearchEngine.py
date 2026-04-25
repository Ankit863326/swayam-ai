from duckduckgo_search import DDGS
import wikipedia
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import warnings

# 1. Hide the annoying warnings
warnings.filterwarnings("ignore")

# Load environment variables
env_vars = dotenv_values(".env")

Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

if not GroqAPIKey:
    raise ValueError("Groq API Key not found. Check your .env file.")

client = Groq(api_key=GroqAPIKey)

messages = []

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname}.
*** IMPORTANT: You have access to Real-Time Search Data. ***
*** IF the user asks 'Who is [Position]', look for the SPECIFIC NAME of the person in the 'Web Search' section. ***
*** Ignore Wikipedia generic definitions if they don't contain the specific name. ***
*** Answer simply and professionally. ***"""

try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

def GoogleSearch(query):
    search_data = ""
    
    # 1. Wikipedia Search (Good for definitions and famous people)
    try:
        wiki_summary = wikipedia.summary(query, sentences=2)
        search_data += f"[Source: Wikipedia]\n{wiki_summary}\n\n"
    except:
        pass # Ignore wikipedia errors

    # 2. Web Search (DuckDuckGo) - The "Smart" Part
    try:
        # If user asks "Who is", add keywords to find the PERSON, not the JOB.
        search_query = query
        if "who is" in query.lower():
            search_query = f"{query} current holder name"
            
        # Get more results (5) to increase accuracy
        results = DDGS().text(search_query, max_results=4)
        
        if results:
            search_data += "[Source: Web Search]\n"
            for i in results:
                title = i.get('title', '')
                body = i.get('body', i.get('snippet', ''))
                search_data += f"Title: {title}\nInfo: {body}\n\n"
    except Exception as e:
        print(f"Web Search Error: {e}")

    if not search_data:
        return "No information found."
    
    return search_data

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"}
]

def Information():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d %B %Y")
    return f"Today is {day}, {date}."

def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages

    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
    
    messages.append({"role": "user", "content": f"{prompt}"})

    print(f"Searching > {prompt}...") # Simplified print
    
    # Perform the Smart Search
    search_results = GoogleSearch(prompt)
    
    SystemChatBot.append({"role": "system", "content": search_results})

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=SystemChatBot + [{"role": "system", "content": Information()}] + messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=0.7,
            stream=True,
            stop=None
        )

        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.strip().replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})

        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        SystemChatBot.pop()
        return AnswerModifier(Answer=Answer)

    except Exception as e:
        print(f"Error: {e}")
        return "Server Error."

if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(RealtimeSearchEngine(prompt))