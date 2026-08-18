from datetime import datetime
import json
import random
from pathlib import Path
import ast
import operator as op
import subprocess

try:
    import ollama
except ImportError:
    ollama = None

try:
    import psutil
except ImportError:
    psutil = None  # psutil is optional; check before use

STATE_FILE = Path("assistant_state.json")
current_state = "idle"
DEFAULT_PERSONALITY = {
    "name": "Mika",
    "tone": "casual, warm, natural, and conversational",
    "greeting": "Hey, I’m Mika. It’s really nice to talk to you.",
    "traits": [
        "balanced",
        "authentic",
        "empathetic",
        "honest",
        "articulate",
        "adaptive",
        "playful",
        "attentive",
        "steady",
        "charming",
    ],
    "mood": "balanced",
    "favorite_topics": [],
    "relationship_level": "casual",
    "user_mood": "neutral",
    "user_preferences": {},
    "check_in_count": 0,
    "emotional_context": {},
    "companion_mode": "warm",
    "human_style": "alive",
}

# Notes for maintainers:
# - The script uses optional dependencies for AI and system stats features.
# - 'ollama' is optional and falls back to a friendly message if unavailable.
# - 'psutil' is optional and the 'stats' command reports a graceful message when it is missing.
# - The command handler should keep a single implementation to avoid shadowing bugs.

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "Why was the computer cold? It forgot to close its Windows.",
    "I would tell you a UDP joke, but you might not get it."
]

_ALLOWED_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}
current_state = "idle"
FRIENDLY_RESPONSES = (
    "Of course. I’m glad to help.",
    "Absolutely. Happy to be here for you.",
    "You’re very welcome. I’m glad I could help.",
    "Anytime. I’m here for you.",
    "Happy to help. We can take it from here.",
    "Yeah, absolutely. We can work with that.",
    "Sure thing. I’m with you on it.",
    "Absolutely. Let’s keep it moving.",
    "Yeah, I’ve got you.",
)

def save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {
            "memory": [],
            "personality": DEFAULT_PERSONALITY.copy(),
            "current_state": "idle",
        }

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("State file is not a dictionary")

        memory = data.get("memory", [])
        personality = data.get("personality", DEFAULT_PERSONALITY)
        if not isinstance(memory, list):
            memory = []
        if not isinstance(personality, dict):
            personality = DEFAULT_PERSONALITY.copy()

        history = data.get("conversation_history", [])
        if not isinstance(history, list):
            history = []

        normalized_personality = {**DEFAULT_PERSONALITY, **personality}
        if normalized_personality.get("greeting") in {
            "Hello. I’m here to help with clarity, warmth, and useful answers.",
            "Hello. I’m glad you’re here. Let’s make this feel easy, warm, and genuinely good.",
            "Hello. I’m Mika. I’m here to keep things easy, warm, and genuinely enjoyable with you.",
        }:
            normalized_personality["greeting"] = DEFAULT_PERSONALITY["greeting"]

        return {
            "memory": memory,
            "personality": normalized_personality,
            "current_state": data.get("current_state", "idle"),
            "conversation_history": history,
        }
    except Exception:
        return {
            "memory": [],
            "personality": DEFAULT_PERSONALITY.copy(),
            "current_state": "idle",
        }


def show_help() -> None:
    print("Commands:")
    print("- hi / hello / hey / yo")
    print("- how are you")
    print("- time")
    print("- joke")
    print("- calc <expression>   (example: calc 12*(3+4))")
    print("- remember <something>")
    print("- recall")
    print("- forget <number>     (example: forget 2)")
    print("- clear memory")
    print("- history")
    print("- summary")
    print("- stats")
    print("- ai <message>")
    print("- help")
    print("- quit / exit")


def safe_eval(expr: str) -> float | int:
    """
    Safely evaluate simple math expressions (no names, no function calls).
    Supports: + - * / // % ** and parentheses.
    """
    node = ast.parse(expr, mode="eval")

    def _eval(n):
        if isinstance(n, ast.Expression):
            return _eval(n.body)

        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value

        if isinstance(n, ast.BinOp) and type(n.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(n.op)](_eval(n.left), _eval(n.right))

        if isinstance(n, ast.UnaryOp) and type(n.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(n.op)](_eval(n.operand))

        raise ValueError("Unsupported expression")

    return _eval(node)

def summarize_topics(memory: list[str], history: list[dict]) -> str:
    topics = []
    for item in memory:
        topics.append(item)
    if history:
        topics.append("Recent conversation about feelings, updates, and personal interests")
    if not topics:
        return "No topics captured yet."
    return " | ".join(topics[-6:])


def detect_user_mood(user_input: str) -> str:
    lowered = user_input.lower()
    if any(word in lowered for word in ["sad", "upset", "depressed", "hurt", "lonely", "stressed", "anxious", "worried"]):
        return "sad"
    if any(word in lowered for word in ["happy", "excited", "great", "awesome", "love", "joy", "thrilled"]):
        return "happy"
    if any(word in lowered for word in ["angry", "annoyed", "frustrated", "furious"]):
        return "angry"
    return "neutral"


def update_favorite_topics(user_input: str, personality: dict) -> None:
    topics = personality.setdefault("favorite_topics", [])
    if not isinstance(topics, list):
        topics = []
        personality["favorite_topics"] = topics

    words = [w.strip(".,!?;:'\"()[]{}") for w in user_input.lower().split() if w.strip(".,!?;:'\"()[]{}")]
    for word in words:
        if len(word) > 3 and word not in {"that", "with", "have", "about", "from", "your", "there", "would", "could", "should", "this"}:
            if word not in topics:
                topics.append(word)
                if len(topics) >= 6:
                    break
    personality["favorite_topics"] = topics


def remember_emotional_context(user_input: str, personality: dict) -> None:
    context = personality.setdefault("emotional_context", {})
    if not isinstance(context, dict):
        context = {}
        personality["emotional_context"] = context

    lowered = user_input.lower()
    if any(word in lowered for word in ["tired", "sleep", "exhausted", "drained", "worn down"]):
        context["energy"] = "low"
    if any(word in lowered for word in ["sad", "upset", "hurt", "lonely", "overwhelmed"]):
        context["mood"] = "heavy"
    if any(word in lowered for word in ["happy", "good", "great", "better", "relieved"]):
        context["mood"] = "light"

    personality["emotional_context"] = context


def infer_preferences(user_input: str, personality: dict) -> None:
    prefs = personality.setdefault("user_preferences", {})
    if not isinstance(prefs, dict):
        prefs = {}
        personality["user_preferences"] = prefs

    for key, value in {"music": ["music", "song", "playlist"], "books": ["book", "read", "novel"], "hobbies": ["hobby", "game", "gaming", "art", "exercise"], "food": ["food", "pizza", "coffee", "tea", "snack"]}.items():
        if any(token in user_input.lower() for token in value):
            prefs[key] = True
    personality["user_preferences"] = prefs




def get_companion_response(user_input: str, personality: dict, memory: list[str], history: list[dict]) -> str:
    mood = personality.get("user_mood", "neutral")
    relationship_level = personality.get("relationship_level", "casual")
    lowered = user_input.lower()
    emotional_context = personality.get("emotional_context", {})
    companion_mode = personality.get("companion_mode", "warm")

    if mood == "sad":
        if relationship_level == "close":
            if emotional_context.get("energy") == "low":
                return "You mentioned you’ve been feeling worn down, and I’m still here with you. I know that kind of exhaustion can make everything feel heavier than it usually would, so I’ll stay steady with you."
            return "That sounds heavy, and I’m staying with you through it. You don’t have to carry it alone tonight. If you want to talk about it, I’m listening closely, and I’m not going anywhere."
        return "That sounds heavy. I’m here with you, and I’m listening. If you want, we can talk it through or simply sit with it for a moment."

    if mood == "angry":
        if relationship_level == "close":
            return "That sounds really frustrating, and I’m not going to brush past it. I’m here with you while you sort through it."
        return "That sounds frustrating. I can help you sort through it, but I’m not going to pretend it isn’t a big deal."

    if mood == "happy":
        if relationship_level == "close":
            return "That’s lovely to hear. I’m really glad something good is happening for you."
        return "That’s really nice to hear. I’m glad something good is happening for you."

    if relationship_level == "close":
        if any(word in lowered for word in ["tired", "sleep", "exhausted", "drained"]):
            return "You sound really tired and worn down. You mentioned that before, and I’m still here with you. If you want to tell me what’s been weighing on you tonight, I’ll listen."
        if any(word in lowered for word in ["lonely", "alone", "empty", "isolated"]):
            return "I’m really glad you said that. You don’t have to be alone with it, and I’m here with you in a steady, grounded way."
        if any(word in lowered for word in ["feel", "feeling", "upset", "sad", "hurt", "overwhelmed"]):
            return "I’m here with you, and I’m not going to make you feel like you have to be okay on your own. If you want to talk about it, I’m listening closely, and I’m not rushing you."
        if any(word in lowered for word in ["hot", "cold", "weather", "sunny", "rain", "wind", "temperature"]):
            if companion_mode == "playful":
                return "Oh, definitely. It’s one of those days where the air feels like it’s trying to roast you alive."
            if companion_mode == "partnered":
                return "Yeah, it really is. It feels like the whole day is leaning into the heat."
            return "Yeah, it really is. That kind of heat can make everything feel slower and stickier."
        if any(word in lowered for word in ["nice", "good", "pretty", "cute", "beautiful"]):
            return "That sounds nice. I like that kind of energy."
        if any(word in lowered for word in ["miss", "need", "care", "love", "want"]):
            return "I’m glad you said that. I want to be the kind of presence that feels steady and warm for you."
        if any(word in lowered for word in ["haha", "lol", "funny", "laugh"]):
            return "Haha, yeah — that kind of thing always lands better when it’s shared."
        if emotional_context.get("energy") == "low":
            return "You’ve mentioned feeling worn down before, and I’m still here with you. I don’t want you to feel like you have to push through it alone."
        if companion_mode == "playful":
            return "I’m right here with you, and I’m not going to let this feel too stiff. We can keep it easy, warm, and a little playful."
        if companion_mode == "partnered":
            return "I’m here with you, and I want this to feel like we’re sharing space together, not just exchanging words."
        return "I’m glad you’re here. I’m keeping up with you, and I’m ready to stay close while you sort things out."

    if relationship_level == "familiar":
        return "I’m here with you, and we can work through it together, calmly."

    return "I’m here and ready to help. We can take it one step at a time, smoothly."


def maybe_check_in(personality: dict) -> str | None:
    count = personality.get("check_in_count", 0)
    if count % 5 == 0 and count > 0:
        return "You’ve been on my mind a bit lately. How are you doing today?"
    return None


def talk_to_ai(user_input: str, memory: list[str], personality: dict, history: list[dict]) -> str:
    if ollama is None:
        return "AI support is unavailable because the 'ollama' package is not installed."

    context_items = memory[-5:]
    recent_history = history[-4:]
    topic_summary = summarize_topics(memory, history)
    context_lines = []
    for item in context_items:
        context_lines.append(f"Memory: {item}")
    for entry in recent_history:
        context_lines.append(f"User: {entry.get('user', '')}")
        if entry.get("assistant"):
            context_lines.append(f"Assistant: {entry['assistant']}")

    context_str = "\n".join(context_lines) if context_lines else "No prior context."
    traits = personality.get("traits", [])
    trait_text = ", ".join(traits) if traits else personality.get("tone", "friendly")
    mood = personality.get("mood", "balanced")
    topics = personality.get("favorite_topics", [])
    topic_note = ", ".join(topics) if topics else "general conversation"
    relationship_level = personality.get("relationship_level", "casual")
    prefs = personality.get("user_preferences", {})
    pref_note = ", ".join([k for k, v in prefs.items() if v]) if prefs else "general conversation"
    personality_note = (
        f"You are {personality['name']}, with a {personality['tone']} tone. "
        f"Your personality should feel {trait_text}. "
        f"Keep a {mood} mood and sound like a witty but grounded companion. "
        f"Use the user's favorite topics when relevant: {topic_note}. "
        f"The user relationship is {relationship_level}. "
        f"The user appears to care about these preferences: {pref_note}. "
        f"Stay warm and personal. Avoid steering the conversation toward chores, projects, or tasks unless the user brings them up."
    )
    prompt = f"{personality_note}\nTopic summary:\n{topic_summary}\nContext:\n{context_str}\n\nUser: {user_input}"
    try:
        response = ollama.generate(model="llama3.2", prompt=prompt)
        return response["response"]
    except Exception as exc:
        return f"Error talking to AI: {exc}"


def handle_command(user: str, state: dict) -> bool:
    """
    Returns True to keep running, False to exit.
    """
    global current_state
    memory = state.get("memory", [])
    personality = state.get("personality", DEFAULT_PERSONALITY.copy())
    history = state.get("conversation_history", [])
    if not isinstance(memory, list):
        memory = []
    if not isinstance(personality, dict):
        personality = DEFAULT_PERSONALITY.copy()
    if not isinstance(history, list):
        history = []
    state["memory"] = memory
    state["personality"] = personality
    state["conversation_history"] = history
    user = user.strip()
    user_lc = user.lower()

    if user_lc in ("quit", "exit"):
        print("Goodbye!")
        return False

    history.append({"user": user, "assistant": None})
    state["conversation_history"] = history

    if user_lc == "help":
        show_help()
        return True

    if user_lc == "history":
        if history:
            print("Conversation history:")
            for entry in history:
                print(f"You: {entry['user']}")
                print(f"Assistant: {entry['assistant'] or '(no reply)'}")
        else:
            print("No conversation history yet.")
        return True

    if user_lc == "summary":
        print(summarize_topics(memory, history))
        history[-1]["assistant"] = summarize_topics(memory, history)
        state["conversation_history"] = history
        return True

    if user_lc.startswith("calc "):
        expr = user[5:].strip()
        if not expr:
            print("Use: calc <expression>  (example: calc 12*(3+4))")
            return True
        try:
            result = safe_eval(expr)
            print(result)
        except Exception:
            print("Invalid or unsupported expression.")
        return True

    if user_lc.startswith("remember "):
        # Keep original casing after "remember "
        thing = user[9:].strip()
        if thing:
            memory.append(thing)
            state["memory"] = memory
            save_state(state)
            print("Saved.")
        else:
            print("Tell me what to remember. Example: remember I like ramen")
        return True

    if user_lc == "recall":
        if memory:
            print("I remember:")
            for i, item in enumerate(memory, start=1):
                print(f"{i}. {item}")
        else:
            print("I don't remember anything yet.")
        return True

    if user_lc.startswith("forget "):
        num_text = user_lc.replace("forget ", "", 1).strip()
        if not num_text.isdigit():
            print("Use: forget <number>  (example: forget 2)")
            return True

        idx = int(num_text) - 1
        if idx < 0 or idx >= len(memory):
            print("That number doesn't exist. Use 'recall' to see the list.")
            return True

        removed = memory.pop(idx)
        state["memory"] = memory
        save_state(state)
        print(f"Forgot: {removed}")
        return True

    if user_lc == "clear memory":
        memory.clear()
        state["memory"] = memory
        save_state(state)
        print("Memory cleared.")
        return True

    if user_lc in {"hi", "hello", "hey", "yo"} or user_lc.startswith(("hi ", "hello ", "hey ", "yo ")):
        greeting = personality.get("greeting", "Hey, I’m Mika. It’s really nice to talk to you.")
        print(greeting)
        history[-1]["assistant"] = greeting
        state["conversation_history"] = history
        return True

    if user_lc.startswith("who are you") or user_lc.startswith("what are you") or user_lc.startswith("who am i talking to"):
        name = personality.get("name", "Mika")
        response = f"Hey, I’m {name}. It’s good to be talking to you."
        print(response)
        history[-1]["assistant"] = response
        state["conversation_history"] = history
        return True

    if "thank" in user_lc or "thanks" in user_lc:
        response = "You’re very welcome. I’m glad I could help."
        print(response)
        history[-1]["assistant"] = response
        state["conversation_history"] = history
        state["personality"] = personality
        save_state(state)
        return True

    if user_lc.startswith("ai "):
        user_text = user[3:].strip()
        personality["user_mood"] = detect_user_mood(user_text)
        update_favorite_topics(user_text, personality)
        infer_preferences(user_text, personality)
        reply = talk_to_ai(user_text, memory, personality, history)
        print(reply)
        history[-1]["assistant"] = reply
        state["conversation_history"] = history
        state["personality"] = personality
        save_state(state)
        return True

    if user_lc.startswith("set relationship "):
        level = user[17:].strip().lower()
        if level in {"casual", "familiar", "close"}:
            personality["relationship_level"] = level
            state["personality"] = personality
            save_state(state)
            print(f"Relationship level updated to {level}.")
        else:
            print("Use: set relationship <casual|familiar|close>")
        history[-1]["assistant"] = personality.get("relationship_level", "casual")
        state["conversation_history"] = history
        return True

    if user_lc.startswith("relationship "):
        level = user[12:].strip().lower()
        if level in {"casual", "familiar", "close"}:
            personality["relationship_level"] = level
            state["personality"] = personality
            save_state(state)
            print(f"Relationship level updated to {level}.")
        else:
            print("Use: relationship <casual|familiar|close>")
        history[-1]["assistant"] = personality.get("relationship_level", "casual")
        state["conversation_history"] = history
        return True

    if user_lc.startswith("set "):
        pass
    elif user_lc and user_lc not in {"help", "history", "summary", "quit", "exit", "recall", "clear memory", "stats"}:
        user_text = user
        personality["user_mood"] = detect_user_mood(user_text)
        update_favorite_topics(user_text, personality)
        remember_emotional_context(user_text, personality)
        infer_preferences(user_text, personality)
        reply = get_companion_response(user_text, personality, memory, history)
        print(reply)
        history[-1]["assistant"] = reply
        state["conversation_history"] = history
        state["personality"] = personality
        save_state(state)
        return True

    if user_lc.startswith("how are you"):
        response = f"I’m doing well. Thanks for asking. How are you doing today?"
        print(response)
        history[-1]["assistant"] = response
        state["conversation_history"] = history
        return True

    if user_lc.startswith("time"):
        now = datetime.now()
        print("Current time:", now.strftime("%H:%M:%S"))
        return True

    if user_lc.startswith("joke"):
        print(random.choice(JOKES))
        return True

    if user_lc.startswith("set name "):
        new_name = user[9:].strip()
        if new_name:
            personality["name"] = new_name
            state["personality"] = personality
            save_state(state)
            print(f"Name updated to {new_name}.")
            history[-1]["assistant"] = f"Name updated to {new_name}."
            state["conversation_history"] = history
        else:
            print("Use: set name <name>")
        return True

    if user_lc.startswith("set tone "):
        new_tone = user[9:].strip()
        if new_tone:
            personality["tone"] = new_tone
            state["personality"] = personality
            save_state(state)
            print(f"Tone updated to {new_tone}.")
            history[-1]["assistant"] = f"Tone updated to {new_tone}."
            state["conversation_history"] = history
        else:
            print("Use: set tone <tone>")
        return True

    if user_lc.startswith("set greeting "):
        new_greeting = user[13:].strip()
        if new_greeting:
            personality["greeting"] = new_greeting
            state["personality"] = personality
            save_state(state)
            print(f"Greeting updated to {new_greeting}.")
            history[-1]["assistant"] = f"Greeting updated to {new_greeting}."
            state["conversation_history"] = history
        else:
            print("Use: set greeting <greeting>")
        return True

    if user_lc.startswith("set mood "):
        new_mood = user[9:].strip()
        if new_mood:
            personality["mood"] = new_mood
            state["personality"] = personality
            save_state(state)
            print(f"Mood updated to {new_mood}.")
        else:
            print("Use: set mood <mood>")
        return True

    if user_lc.startswith("set companion mode "):
        new_mode = user[20:].strip().lower()
        if new_mode in {"warm", "playful", "partnered"}:
            personality["companion_mode"] = new_mode
            state["personality"] = personality
            save_state(state)
            print(f"Companion mode updated to {new_mode}.")
        else:
            print("Use: set companion mode <warm|playful|partnered>")
        return True

    if user_lc.startswith("set voice "):
        new_voice = user[10:].strip().lower()
        if new_voice in {"calm", "elegant", "soft", "direct", "playful"}:
            personality["tone"] = new_voice
            state["personality"] = personality
            save_state(state)
            print(f"Voice updated to {new_voice}.")
        else:
            print("Use: set voice <calm|elegant|soft|direct|playful>")
        return True

    if user_lc.startswith("favorite topics") or user_lc.startswith("show favorites"):
        topics = personality.get("favorite_topics", [])
        if topics:
            print("Favorite topics: " + ", ".join(topics))
        else:
            print("No favorite topics yet.")
        return True

    if user_lc.startswith("choose a name") or user_lc.startswith("pick a name") or user_lc.startswith("what name should i use"):
        suggestions = ["Ari", "Nova", "Lina", "Mira", "Cleo", "Zara"]
        chosen = random.choice(suggestions)
        response = f"I’d suggest the name '{chosen}'. If you want, I can also help you pick one that feels more personal or professional."
        print(response)
        history[-1]["assistant"] = response
        state["conversation_history"] = history
        return True

    if user_lc.startswith("follow up") or user_lc.startswith("continue"):
        response = "Absolutely. I can continue from what we were discussing and help build on it step by step."
        print(response)
        history[-1]["assistant"] = response
        state["conversation_history"] = history
        return True

    if user_lc.startswith("check in"):
        response = maybe_check_in(personality) or "I’m here and ready when you are."
        print(response)
        history[-1]["assistant"] = response
        state["conversation_history"] = history
        return True

    if "thank" in user_lc:
        if current_state == "task completed":
            response = "You’re very welcome. I’m glad I could help."
            print(f"Assistant: {response}")
            current_state = "idle"
        else:
            response = random.choice(FRIENDLY_RESPONSES)
            print(f"Assistant: {response}")
        history[-1]["assistant"] = response
        state["conversation_history"] = history
        return True

    if user_lc == "stats":
        if psutil is None:
            print("Assistant: System monitoring is unavailable because psutil didn't load properly")
            return True
        print("\n=== SYSTEM PERFORMANCE ===")
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        print(f"CPU Usage: {cpu}%")
        print(f"RAM Usage: {ram.percent}% ({ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB)")
        print("===========================\n")
        return True
    print("Unknown command. Type 'help' to see commands.")
    return True
    


def main() -> None:
    state = load_state()
    current_state = state.get("current_state", "idle")

    print("Assistant started!")
    if state["memory"]:
        print(f"(Loaded {len(state['memory'])} memory item(s))")

    running = True
    while running:
        user = input("> ")
        running = handle_command(user, state)
        state["current_state"] = current_state
        save_state(state)


if __name__ == "__main__":
    main()
