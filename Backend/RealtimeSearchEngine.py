import os
import time
import datetime
import warnings
from json import load, dump
from dotenv import load_dotenv
from groq import Groq

warnings.filterwarnings("ignore")

# ── Config ───────────────────────────────────────────────────
load_dotenv()

Username      = os.getenv("Username",      "User")
AssistantName = os.getenv("Assistantname", "Swayam")
GroqAPIKey    = os.getenv("GroqAPIKey",    "")

if not GroqAPIKey:
    raise ValueError("GroqAPIKey not found in .env file.")

client = Groq(api_key=GroqAPIKey)

CHAT_LOG    = os.path.join("Data", "ChatLog.json")
MAX_HISTORY = 20

# ── Search result cache ───────────────────────────────────────
_search_cache: dict = {}
CACHE_TTL = 300   # 5 minutes

# ── System prompt ─────────────────────────────────────────────
System = f"""You are {AssistantName}, an advanced AI assistant for {Username}.
You have access to real-time web search results provided in the context.

RULES:
- Use the search results to give accurate, up-to-date answers.
- If the user asks "Who is [position]", find the SPECIFIC PERSON's name from search data.
- Ignore Wikipedia generic definitions when web search has the specific answer.
- Be concise and professional. Do not add unnecessary commentary.
- If search results do not contain the answer, say so clearly and give your best knowledge.
- Never fabricate facts. Always prefer search data over your training data for current events.
"""

SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user",      "content": "Hi"},
    {"role": "assistant", "content": f"Hello {Username}, I am ready to search the web for you."},
]

os.makedirs("Data", exist_ok=True)
if not os.path.exists(CHAT_LOG):
    with open(CHAT_LOG, "w", encoding="utf-8") as f:
        dump([], f)


# ── Web search ────────────────────────────────────────────────
def GoogleSearch(query: str) -> str:
    """Search DuckDuckGo + Wikipedia with 5-minute caching."""
    global _search_cache

    now = time.time()
    if query in _search_cache:
        cached_time, cached_result = _search_cache[query]
        if now - cached_time < CACHE_TTL:
            print(f"[Cache] Hit for: {query}")
            return cached_result

    search_data = ""

    # 1. Wikipedia
    try:
        import wikipedia
        wiki = wikipedia.summary(query, sentences=2, auto_suggest=False)
        search_data += f"[Wikipedia]\n{wiki}\n\n"
    except Exception:
        pass

    # 2. DuckDuckGo
    try:
        from duckduckgo_search import DDGS
        search_query = query
        if "who is" in query.lower():
            search_query = f"{query} current person name 2024"
        results = DDGS().text(search_query, max_results=5)
        if results:
            search_data += "[Web Search]\n"
            for r in results:
                title = r.get("title", "")
                body  = r.get("body", r.get("snippet", ""))
                search_data += f"Title: {title}\nInfo: {body}\n\n"
    except Exception as e:
        print(f"[DuckDuckGo Error] {e}")

    result = search_data.strip() if search_data.strip() else "No search results found."
    _search_cache[query] = (now, result)
    return result


# ── Helpers ───────────────────────────────────────────────────
def AnswerModifier(Answer: str) -> str:
    return "\n".join(l for l in Answer.split("\n") if l.strip())


def CurrentDateTime() -> str:
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A, %d %B %Y')}. Time: {now.strftime('%H:%M')}."


# ── Main search engine function ───────────────────────────────
def RealtimeSearchEngine(prompt: str) -> str:
    global SystemChatBot

    with open(CHAT_LOG, "r", encoding="utf-8") as f:
        messages = load(f)

    messages = messages[-MAX_HISTORY:]
    messages.append({"role": "user", "content": prompt})

    print(f"[Search] {prompt}")
    search_results = GoogleSearch(prompt)

    # inject search results into system
    SystemChatBot_with_search = SystemChatBot + [
        {"role": "system", "content": f"Search Results:\n{search_results}"},
        {"role": "system", "content": CurrentDateTime()},
    ]

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=SystemChatBot_with_search + messages,
            temperature=0.65,
            max_tokens=2048,
            top_p=0.9,
            stream=True,
            stop=None,
        )

        Answer = ""
        for chunk in completion:
            delta = chunk.choices[0].delta.content
            if delta:
                Answer += delta

        Answer = Answer.strip().replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})

        with open(CHAT_LOG, "w", encoding="utf-8") as f:
            dump(messages, f, indent=4, ensure_ascii=False)

        return AnswerModifier(Answer)

    except Exception as e:
        print(f"[SearchEngine Error] {e}")
        return "Search failed. Please check your internet connection and try again."


# ── CLI test ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("Realtime Search Engine — type 'exit' to quit\n")
    while True:
        q = input("Query: ").strip()
        if q.lower() in ["exit", "quit"]:
            break
        if q:
            print(f"\nAnswer: {RealtimeSearchEngine(q)}\n")