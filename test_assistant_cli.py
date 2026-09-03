import importlib.util
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location("assistant_cli", Path(__file__).with_name("assistant_cli.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fresh_state():
    return {
        "memory": [],
        "personality": deepcopy(module.DEFAULT_PERSONALITY),
        "current_state": "idle",
        "conversation_history": [],
    }


def test_safe_eval_basic_math():
    assert module.safe_eval("2 + 3 * 4") == 14


def test_detect_user_mood():
    assert module.detect_user_mood("I am really happy today") == "happy"


def test_handle_command_greeting():
    state = fresh_state()
    response = module.handle_command("hello", state)
    assert "Lumina" in response or "Hey" in response or "hello" in response.lower()


def test_handle_command_remember():
    state = fresh_state()
    response = module.handle_command("remember I like tea", state)
    assert "tea" in response.lower()
    assert any("tea" in item.lower() for item in state["memory"])


def test_fun_commands_return_engaging_content():
    state = fresh_state()

    assert module.handle_command("joke", state) in module.JOKES
    assert module.handle_command("fun fact", state) in module.TECH_TIPS


def test_personality_growth_tracks_interactions():
    state = fresh_state()

    for _ in range(5):
        module.handle_command("hello", state)

    evolution = state["personality"]["evolution"]
    assert evolution["interaction_count"] == 5
    assert evolution["stage"] == "familiar"


def test_memory_and_summary_commands_work_together():
    state = fresh_state()

    module.handle_command("remember I like Python", state)
    response = module.handle_command("summary", state)

    assert "Current mood: balanced" in response
    assert "I like Python" in response


def test_normal_conversation_updates_persistent_profile():
    state = fresh_state()

    module.handle_command("I am tired and I love music", state)

    personality = state["personality"]
    assert personality["emotional_context"]["energy"] == "low"
    assert personality["user_preferences"]["music"] is True


def test_lumina_prefix_uses_ai_path():
    state = fresh_state()

    class FakeOllama:
        @staticmethod
        def chat(model, messages):
            assert model == "llama3.2"
            assert messages[0]["role"] == "system"
            assert "Lumina" in messages[0]["content"]
            assert "Relationship level: casual" in messages[0]["content"]
            assert "User preferences" in messages[0]["content"]
            assert messages[-1] == {"role": "user", "content": "Explain recursion"}
            return SimpleNamespace(
                message=SimpleNamespace(content="Recursion is a function calling itself.")
            )

    original_ollama = module.ollama
    module.ollama = FakeOllama()
    try:
        response = module.handle_command("Lumina, Explain recursion", state)
    finally:
        module.ollama = original_ollama

    assert response == "Recursion is a function calling itself."
