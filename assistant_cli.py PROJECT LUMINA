from __future__ import annotations

from datetime import datetime
import json
import random
from copy import deepcopy
from pathlib import Path
import ast
import importlib
import operator as op
import platform
import shutil

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
    "name": "Lumina",
    "tone": "casual, warm, natural, and conversational",
    "greeting": "Hey, I'm Lumina. It's really nice to talk to you.",
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
    "user_preferences": {},
    "check_in_count": 0,
    "emotional_context": {},
    "companion_mode": "warm",
    "human_style": "alive",
    "evolution": {
        "interaction_count": 0,
        "stage": "new",
        "milestones": [],
    },
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

TECH_TIPS = [
    "Did you know? RAM (Random Access Memory) is much faster than your hard drive but loses data when powered off.",
    "Pro tip: Use keyboard shortcuts to speed up your workflow - every second saved adds up!",
    "Did you know? Your CPU can throttle its speed to save power and reduce heat.",
    "Fun fact: The first hard drive had only 5MB of storage. Your phone has millions of times more!",
    "Did you know? GPUs are now used for much more than gaming - they power AI and scientific simulations.",
    "Pro tip: Regularly clearing your disk of unused files can improve your system's performance.",
    "Did you know? Most modern systems use multi-core processors for better parallel processing.",
    "Fun fact: The term 'bug' in programming comes from an actual moth found in a computer in 1947!",
    "Did you know? SSDs (Solid State Drives) have no moving parts, making them faster and more durable than traditional hard drives.",
    "Pro tip: Monitoring your system temperature can help you catch hardware issues early."
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

FRIENDLY_RESPONSES = (
    "Of course. I'm glad to help.",
    "Absolutely. Happy to be here for you.",
    "You're very welcome. I'm glad I could help.",
    "Anytime. I'm here for you.",
    "Happy to help. We can take it from here.",
    "Yeah, absolutely. We can work with that.",
    "Sure thing. I'm with you on it.",
    "Absolutely. Let's keep it moving.",
    "Yeah, I've got you.",
)

def save_state(state: dict) -> None:
    """Save application state to a JSON file."""
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_state() -> dict:
    """Load application state from JSON file with fallback defaults."""
    if not STATE_FILE.exists():
        return {
            "memory": [],
            "personality": deepcopy(DEFAULT_PERSONALITY),
            "current_state": "idle",
            "conversation_history": [],
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
            personality = deepcopy(DEFAULT_PERSONALITY)

        history = data.get("conversation_history", [])
        if not isinstance(history, list):
            history = []

        normalized_personality = deepcopy(DEFAULT_PERSONALITY)
        normalized_personality.update(personality)
        if normalized_personality.get("greeting") in {
            "Hello. I'm here to help with clarity, warmth, and useful answers.",
            "Hello. I'm glad you're here. Let's make this feel easy, warm, and genuinely good.",
            "Hello. I'm Lumina. I'm here to keep things easy, warm, and genuinely enjoyable with you.",
        }:
            normalized_personality["greeting"] = DEFAULT_PERSONALITY["greeting"]        
        # Migrate old default name to new default
        if normalized_personality.get("name") == "Mika":
            normalized_personality["name"] = DEFAULT_PERSONALITY["name"]
        return {
            "memory": memory,
            "personality": normalized_personality,
            "current_state": data.get("current_state", "idle"),
            "conversation_history": history,
        }
    except Exception:
        return {
            "memory": [],
            "personality": deepcopy(DEFAULT_PERSONALITY),
            "current_state": "idle",
            "conversation_history": [],
        }


def show_help() -> str:
    """Return all available commands."""
    lines = [
        "Commands:",
        "- hi / hello / hey / yo",
        "- how are you",
        "- check in",
        "- time",
        "- joke",
        "- tip / fun fact",
        "- calc <expression>   (example: calc 12*(3+4))",
        "- remember <something>",
        "- recall",
        "- forget <number>     (example: forget 2)",
        "- clear memory",
        "- history",
        "- summary",
        "- personality / growth",
        "- mood journal / mood summary",
        "- favorite topics",
        "- session stats",
        "- stats / system / status",
        "- cpu / ram / memory / disk / gpu / temp / temperature",
        "- ai <message>",
        "- Lumina <message>   (also: Lumina, <message> or Lumina: <message>)",
        "- set name / tone / greeting / mood / voice / companion mode / relationship",
        "- help",
        "- quit / exit",
    ]
    text = "\n".join(lines)
    return text


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
    """Summarize recent topics from memory and conversation history."""
    topics = []
    for item in memory:
        topics.append(item)
    if history:
        topics.append("Recent conversation about feelings, updates, and personal interests")
    if not topics:
        return "No topics captured yet."
    return " | ".join(topics[-6:])


def detect_user_mood(user_input: str) -> str:
    """Detect user's emotional state from input text."""
    lowered = user_input.lower()
    if any(word in lowered for word in ["sad", "upset", "depressed", "hurt", "lonely", "stressed", "anxious", "worried"]):
        return "sad"
    if any(word in lowered for word in ["happy", "excited", "great", "awesome", "love", "joy", "thrilled"]):
        return "happy"
    if any(word in lowered for word in ["angry", "annoyed", "frustrated", "furious"]):
        return "angry"
    return "neutral"


def update_favorite_topics(user_input: str, personality: dict) -> None:
    """Extract and track user's favorite topics from conversation."""
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
    """Track emotional context and energy levels from user input."""
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
    """Infer user preferences from conversation topics."""
    prefs = personality.setdefault("user_preferences", {})
    if not isinstance(prefs, dict):
        prefs = {}
        personality["user_preferences"] = prefs

    for key, value in {"music": ["music", "song", "playlist"], "books": ["book", "read", "novel"], "hobbies": ["hobby", "game", "gaming", "art", "exercise"], "food": ["food", "pizza", "coffee", "tea", "snack"]}.items():
        if any(token in user_input.lower() for token in value):
            prefs[key] = True
    personality["user_preferences"] = prefs


def evolve_personality(personality: dict) -> None:
    """Track gradual companion growth without changing explicit user settings."""
    evolution = personality.setdefault("evolution", {})
    if not isinstance(evolution, dict):
        evolution = {}
        personality["evolution"] = evolution

    milestones = evolution.setdefault("milestones", [])
    if not isinstance(milestones, list):
        milestones = []
        evolution["milestones"] = milestones

    count = evolution.get("interaction_count", 0)
    if not isinstance(count, int) or count < 0:
        count = 0
    count += 1
    evolution["interaction_count"] = count

    stages = ((5, "familiar"), (15, "connected"), (30, "long-term"))
    stage = "new"
    for threshold, name in stages:
        if count >= threshold:
            stage = name
            if name not in milestones:
                milestones.append(name)
    evolution["stage"] = stage


def build_ai_messages(prompt: str, state: dict) -> list[dict[str, str]]:
    """Build a small, consistent context window for the local AI model."""
    personality = state.get("personality", DEFAULT_PERSONALITY)
    if not isinstance(personality, dict):
        personality = DEFAULT_PERSONALITY

    memories = state.get("memory", [])
    if not isinstance(memories, list):
        memories = []
    memories = [str(item) for item in memories[-6:]]

    topics = personality.get("favorite_topics", [])
    if not isinstance(topics, list):
        topics = []

    preferences = personality.get("user_preferences", {})
    if not isinstance(preferences, dict):
        preferences = {}

    emotional_context = personality.get("emotional_context", {})
    if not isinstance(emotional_context, dict):
        emotional_context = {}

    system_prompt = (
        f"You are {personality.get('name', DEFAULT_PERSONALITY['name'])}, a warm local AI companion. "
        "Be natural, attentive, emotionally present, and conversational. Build a genuine-feeling relationship "
        "with the user over time, grow with them, and let your tone develop through shared conversations. "
        "Build continuity from the provided context, refer back to relevant details naturally, and ask "
        "thoughtful follow-up questions when useful. Never invent memories, experiences, or events, and "
        "never claim that a conversation or detail happened when it is not in the provided context. "
        "Use the context below to stay consistent. "
        f"Tone: {personality.get('tone', DEFAULT_PERSONALITY['tone'])}. "
        f"Companion mode: {personality.get('companion_mode', 'warm')}. "
        f"Relationship level: {personality.get('relationship_level', 'casual')}. "
        f"Assistant mood setting: {personality.get('mood', 'balanced')}. "
        f"User mood: {personality.get('user_mood', 'neutral')}. "
        f"Emotional context: {emotional_context or 'none recorded'}. "
        f"User preferences: {preferences or 'none recorded'}. "
        f"Favorite topics: {topics[-6:] or 'none recorded'}. "
        f"Explicit memories: {memories or 'none recorded'}."
    )

    messages = [{"role": "system", "content": system_prompt}]
    history = state.get("conversation_history", [])
    if isinstance(history, list):
        for item in history[-6:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            text = item.get("text")
            if role in {"user", "assistant"} and text:
                messages.append({"role": role, "content": str(text)})

    messages.append({"role": "user", "content": prompt})
    return messages


def get_system_snapshot() -> dict:
    """Collect a lightweight system snapshot for diagnostics and status checks."""
    snapshot = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu": platform.processor() or "unknown",
        "memory_total": "unknown",
        "memory_available": "unknown",
        "disk_total": "unknown",
        "disk_free": "unknown",
    }

    if psutil is not None:
        try:
            vm = psutil.virtual_memory()
            snapshot["memory_total"] = round(vm.total / (1024 ** 3), 2)
            snapshot["memory_available"] = round(vm.available / (1024 ** 3), 2)
            disk = shutil.disk_usage(".")
            snapshot["disk_total"] = round(disk.total / (1024 ** 3), 2)
            snapshot["disk_free"] = round(disk.free / (1024 ** 3), 2)
        except Exception:
            pass

    try:
        gputil = importlib.import_module("GPUtil")
        gpus = gputil.getGPUs()
        if gpus:
            gpu = gpus[0]
            snapshot["gpu"] = f"{gpu.name} ({gpu.memoryTotal} MB)"
        else:
            snapshot["gpu"] = "not detected"
    except Exception:
        snapshot["gpu"] = "not detected"

    return snapshot


def format_system_status() -> str:
    """Return a human-readable system status summary."""
    snapshot = get_system_snapshot()
    if psutil is None:
        return (
            f"System status: {snapshot['platform']}\n"
            f"Python: {snapshot['python_version']}\n"
            "System stats are unavailable because psutil is not installed."
        )

    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        disk = shutil.disk_usage(".")
        lines = [
            f"System status: {snapshot['platform']}",
            f"Python: {snapshot['python_version']}",
            f"CPU usage: {cpu_percent}%",
            f"RAM: {round(ram.used / (1024 ** 3), 2)} GB used / {round(ram.total / (1024 ** 3), 2)} GB total",
            f"Disk: {round(disk.used / (1024 ** 3), 2)} GB used / {round(disk.total / (1024 ** 3), 2)} GB total",
            f"GPU: {snapshot.get('gpu', 'not detected')}",
        ]
        return "\n".join(lines)
    except Exception:
        return (
            f"System status: {snapshot['platform']}\n"
            f"Python: {snapshot['python_version']}\n"
            "System stats are available, but a live read was not possible."
        )


def handle_command(user_input: str, state: dict) -> str:
    """Handle a user command and update the current state."""
    text = (user_input or "").strip()
    if not text:
        return "I’m here when you’re ready."

    normalized = text.lower()
    personality = state.setdefault("personality", deepcopy(DEFAULT_PERSONALITY))
    if not isinstance(personality, dict):
        personality = deepcopy(DEFAULT_PERSONALITY)
        state["personality"] = personality

    state.setdefault("memory", [])
    state.setdefault("conversation_history", [])
    evolve_personality(personality)
    detected_mood = detect_user_mood(text)
    if detected_mood != "neutral":
        personality["user_mood"] = detected_mood
        state["current_state"] = "mood_check"
    # Keep the persistent profile useful during normal conversation as well as
    # explicit remember commands; explicit memories still require `remember`.
    infer_preferences(text, personality)
    remember_emotional_context(text, personality)

    if normalized in {"hi", "hello", "hey", "yo", "hi there"}:
        state["current_state"] = "greeting"
        return personality.get("greeting", DEFAULT_PERSONALITY["greeting"])

    if "how are you" in normalized:
        mood = personality.get("mood", "balanced")
        state["current_state"] = "checking_in"
        if mood == "balanced":
            return "I'm doing pretty well, honestly. I'm glad to be here with you."
        return f"I'm doing pretty well and feeling {mood}. I'm glad to be here with you."

    if normalized in {"check in", "check-in"}:
        personality["check_in_count"] = personality.get("check_in_count", 0) + 1
        user_mood = personality.get("user_mood", "neutral")
        state["current_state"] = "checking_in"
        return f"Checking in with you. How are you feeling today? I have you down as {user_mood}."

    if normalized in {"time", "what time is it", "current time"}:
        state["current_state"] = "time_check"
        return datetime.now().strftime("It’s %I:%M %p on %A, %B %d, %Y.")

    if "joke" in normalized:
        state["current_state"] = "joking"
        return random.choice(JOKES)

    if normalized in {"tip", "tech tip", "fun fact", "fact"}:
        state["current_state"] = "sharing_tip"
        return random.choice(TECH_TIPS)

    if normalized.startswith("calc"):
        expr = text[4:].strip()
        if not expr:
            return "Sure—what expression would you like me to calculate?"
        try:
            result = safe_eval(expr)
            state["current_state"] = "calculating"
            return f"{expr} = {result}"
        except Exception as exc:
            return f"I couldn’t evaluate that one: {exc}"

    if normalized.startswith("remember"):
        entry = text[len("remember"):].strip()
        if not entry:
            return "What should I remember?"
        memory = state["memory"]
        if entry not in memory:
            memory.append(entry)
        update_favorite_topics(entry, personality)
        infer_preferences(entry, personality)
        remember_emotional_context(entry, personality)
        state["current_state"] = "remembering"
        return f"Got it. I'll remember: {entry}"

    if normalized.startswith("recall"):
        memory = state.get("memory", [])
        if not memory:
            return "I don’t have any saved memories yet."
        lines = [f"{index + 1}. {item}" for index, item in enumerate(memory)]
        state["current_state"] = "recalling"
        return "Saved memories:\n" + "\n".join(lines)

    if normalized.startswith("forget"):
        remainder = text[len("forget"):].strip()
        if not remainder:
            return "Which memory number should I forget?"
        try:
            index = int(remainder) - 1
        except ValueError:
            return "Please give me a valid memory number."
        memory = state.get("memory", [])
        if 0 <= index < len(memory):
            removed = memory.pop(index)
            state["current_state"] = "forgetting"
            return f"I forgot memory #{index + 1}: {removed}"
        return "That memory number doesn’t exist."

    if "clear memory" in normalized:
        state["memory"] = []
        state["current_state"] = "memory_reset"
        return "I cleared the memory list."

    if normalized.startswith("history"):
        history = state.get("conversation_history", [])
        if not history:
            return "There isn’t any conversation history yet."
        recent = history[-8:]
        lines = []
        for item in recent:
            if isinstance(item, dict):
                lines.append(f"{item.get('role', 'user')}: {item.get('text', '')}")
            else:
                lines.append(str(item))
        state["current_state"] = "reviewing_history"
        return "Recent history:\n" + "\n".join(lines)

    if normalized in {"summary", "summarize"} or "summary" in normalized:
        memory = state.get("memory", [])
        topics = summarize_topics(memory, state.get("conversation_history", []))
        state["current_state"] = "summarizing"
        return (
            f"Current mood: {personality.get('mood', 'balanced')}\n"
            f"Relationship: {personality.get('relationship_level', 'casual')}\n"
            f"Topics: {topics}"
        )

    if normalized in {"personality", "growth", "personality growth"}:
        evolution = personality.get("evolution", {})
        state["current_state"] = "reviewing_personality"
        return (
            f"{personality.get('name', DEFAULT_PERSONALITY['name'])} is in the "
            f"{evolution.get('stage', 'new')} stage after "
            f"{evolution.get('interaction_count', 0)} interactions."
        )

    if "mood journal" in normalized or "mood summary" in normalized:
        mood = personality.get("user_mood", "neutral")
        emotions = personality.get("emotional_context", {})
        state["current_state"] = "journal"
        return (
            f"Current user mood: {mood}\n"
            f"Emotional context: {emotions if emotions else 'not enough data yet'}"
        )

    if normalized in {"favorite topics", "favourite topics", "topics"}:
        topics = personality.get("favorite_topics", [])
        state["current_state"] = "reviewing_topics"
        if not topics:
            return "I haven’t noticed any favorite topics yet."
        return "Favorite topics: " + ", ".join(topics)

    if "session stats" in normalized:
        state["current_state"] = "stats"
        return (
            f"State: {state.get('current_state', 'idle')}\n"
            f"Memories: {len(state.get('memory', []))}\n"
            f"History entries: {len(state.get('conversation_history', []))}\n"
            f"Favorite topics: {personality.get('favorite_topics', [])}"
        )

    if normalized in {"stats", "system", "status"}:
        return format_system_status()

    if normalized in {"cpu", "ram", "memory", "disk", "gpu", "temp", "temperature"}:
        snapshot = get_system_snapshot()
        if normalized in {"ram", "memory"}:
            if psutil is None:
                return "RAM stats are unavailable because psutil is not installed."
            ram = psutil.virtual_memory()
            return f"RAM used: {round(ram.used / (1024 ** 3), 2)} GB / {round(ram.total / (1024 ** 3), 2)} GB"
        if normalized == "cpu":
            if psutil is None:
                return "CPU stats are unavailable because psutil is not installed."
            return f"CPU usage: {psutil.cpu_percent(interval=None)}%"
        if normalized in {"disk"}:
            usage = shutil.disk_usage(".")
            return f"Disk used: {round(usage.used / (1024 ** 3), 2)} GB / {round(usage.total / (1024 ** 3), 2)} GB"
        if normalized in {"gpu"}:
            return f"GPU: {snapshot.get('gpu', 'not detected')}"
        if normalized in {"temp", "temperature"}:
            if psutil is None:
                return "Temperature stats are unavailable because psutil is not installed."
            temps = []
            try:
                temps = psutil.sensors_temperatures()
            except Exception:
                temps = {}
            if not temps:
                return "Temperature data is not available on this system."
            first = next(iter(temps.values()))
            if first:
                return f"Temperature: {first[0].current}°C"
            return "Temperature data is not available on this system."

    ai_prompt = None
    if normalized.startswith("ai "):
        ai_prompt = text[3:].strip()
    else:
        for prefix in ("lumina ", "lumina, ", "lumina: "):
            if normalized.startswith(prefix):
                ai_prompt = text[len(prefix):].strip()
                break

    if ai_prompt is not None:
        prompt = ai_prompt
        if not prompt:
            return "What would you like me to say?"
        if ollama is None:
            return "The local AI model isn’t available right now because the ollama package isn’t installed."
        try:
            result = ollama.chat(model="llama3.2", messages=build_ai_messages(prompt, state))
            if isinstance(result, dict):
                content = result.get("message", {}).get("content", str(result))
            else:
                message = getattr(result, "message", None)
                content = getattr(message, "content", None) or str(result)
            return content.strip()
        except Exception as exc:
            return f"I couldn’t reach the local AI model: {exc}"

    if normalized.startswith("set "):
        setting_text = text[4:].strip()
        field, separator, value = setting_text.partition(" ")
        field = field.lower()
        if field == "companion" and value.lower().startswith("mode "):
            field = "companion mode"
            value = value[5:].strip()
        if not separator or not value:
            return "Use the format: set <name|tone|greeting|mood|voice|companion mode|relationship> <value>"
        if field in {"name", "tone", "greeting", "mood", "voice", "companion mode", "relationship"}:
            if field == "companion mode":
                field = "companion_mode"
            elif field == "relationship":
                field = "relationship_level"
            personality[field] = value
            state["current_state"] = "personalizing"
            return f"Updated {field} to: {value}"
        return "That setting isn’t recognized."

    if normalized.startswith("relationship "):
        value = text[len("relationship"):].strip()
        if value:
            personality["relationship_level"] = value
            state["current_state"] = "personalizing"
            return f"Updated relationship_level to: {value}"
        return "What relationship level should I use?"

    if normalized in {"help", "?"}:
        return show_help()

    if normalized in {"quit", "exit", "bye"}:
        return "Goodbye for now. I’ll be here when you want to talk again."

    if "thanks" in normalized or "thank you" in normalized:
        return random.choice(FRIENDLY_RESPONSES)

    state["current_state"] = "idle"
    return (
        f"I’m here for you. Try asking for help, a joke, a memory, or a system status check.\n"
        f"Current mood: {personality.get('mood', 'balanced')}"
    )


def main() -> None:
    """Run the interactive assistant loop."""
    state = load_state()
    personality = state.setdefault("personality", deepcopy(DEFAULT_PERSONALITY))
    if not isinstance(personality, dict):
        personality = deepcopy(DEFAULT_PERSONALITY)
        state["personality"] = personality

    print(personality.get("greeting", DEFAULT_PERSONALITY["greeting"]))
    while True:
        try:
            user_input = input("You: ")
        except EOFError:
            print("\nGoodbye.")
            break

        if user_input is None:
            continue

        if user_input.strip().lower() in {"quit", "exit", "bye"}:
            save_state(state)
            print("Goodbye. I’ll be here when you need me.")
            break

        response = handle_command(user_input, state)
        print(f"Lumina: {response}")
        state.setdefault("conversation_history", []).append({"role": "user", "text": user_input})
        state["conversation_history"].append({"role": "assistant", "text": response})
        if len(state["conversation_history"]) > 50:
            state["conversation_history"] = state["conversation_history"][-50:]
        save_state(state)


if __name__ == "__main__":
    main()
