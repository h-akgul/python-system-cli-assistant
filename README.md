# Assistant CLI

A conversational AI assistant with personality, memory, and mood-aware responses. Built with Python, featuring local AI integration via Ollama and system monitoring capabilities.

## Features

- **Persistent Memory**: Remember facts about the user across sessions
- **Dynamic Personality**: Customize the assistant's name, tone, and greeting
- **Mood Detection**: Responds differently based on emotional context
- **Relationship Levels**: Adjust response style (casual, familiar, close)
- **AI Integration**: Optional Ollama AI backend for intelligent responses
- **System Stats**: Monitor CPU, memory, disk, GPU, and temperature when supported
- **Safe Math Evaluation**: Evaluate mathematical expressions safely
- **Conversation History**: Track conversation history per session
- **Fun and Engagement**: Jokes, tech tips, check-ins, mood journaling, summaries, and personality growth

## Installation

### Requirements
- Python 3.10+

### Optional Dependencies
- **Ollama** (for AI responses): `pip install ollama`
  - Requires Ollama service running (download from [ollama.ai](https://ollama.ai))
  - Model: `llama3.2` (auto-fetched on first use)
  
- **psutil** (for system stats): `pip install psutil`
- **GPUtil** (optional GPU detection): `pip install GPUtil`

### Quick Start
```bash
# Open the project folder
cd PythonProjects

# Run the assistant
python assistant_cli.py
```

## Usage

### Basic Commands

| Command | Description |
|---------|-------------|
| `hi`, `hello`, `hey`, `yo` | Greet the assistant |
| `how are you` | Ask how the assistant is doing |
| `time` | Show current time |
| `joke` | Get a random programmer joke |
| `tip`, `fun fact` | Get a random technology tip or fact |
| `how are you` | Ask how the assistant is doing |
| `help` | Display all commands |
| `quit`, `exit` | Exit the program |

### Memory Commands

| Command | Description |
|---------|-------------|
| `remember <something>` | Save something to memory |
| `recall` | List all remembered items |
| `forget <number>` | Remove a specific memory item |
| `clear memory` | Clear all memories |

### Conversation Commands

| Command | Description |
|---------|-------------|
| `history` | View conversation history |
| `summary` | Summarize topics discussed |
| `ai <message>` | Send message to AI model |
| `Lumina <message>` | Send a natural-language request to the AI model; commas and colons also work |
| `check in` | Receive a check-in message |
| `mood journal`, `mood summary` | Review detected mood and emotional context |
| `personality`, `growth` | Review personality growth |
| `session stats` | Review memories, history, and tracked topics |

### Customization Commands

| Command | Description |
|---------|-------------|
| `set name <name>` | Change assistant name |
| `set tone <tone>` | Change response tone |
| `set greeting <greeting>` | Set custom greeting |
| `set mood <mood>` | Set assistant mood |
| `set companion mode <mode>` | Set response style: `warm`, `playful`, or `partnered` |
| `relationship <level>` | Set relationship level: `casual`, `familiar`, or `close` |

### Other Commands

| Command | Description |
|---------|-------------|
| `calc <expression>` | Evaluate math expressions (e.g., `calc 12*(3+4)`) |
| `stats` | Show CPU and memory usage |
| `favorite topics` | Show detected favorite topics |

## Examples

```
> hi
Hey, I'm Lumina. It's really nice to talk to you.

> remember I like Python
Got it. I'll remember: I like Python

> calc 2**10
2**10 = 1024

> set companion mode playful
Companion mode updated to playful.

> ai Tell me about recursion
[AI response from Ollama model]

> recall
I remember:
1. I like Python
```

## Architecture

### State Management
- Application state (memory, personality, conversation history) is automatically saved to `assistant_state.json`
- State persists between sessions
- Graceful fallback to defaults if state file is corrupted

### Safe Evaluation
- Math expressions are evaluated using AST parsing (no `eval()`)
- Supports: `+`, `-`, `*`, `/`, `//`, `%`, `**`, and parentheses
- Completely sandboxed for security

### Optional Dependencies
- Features gracefully degrade if optional packages aren't installed
- AI responses return friendly message if Ollama is unavailable
- System stats show helpful message if psutil is unavailable

## Development

### Code Structure
- **State Management**: `save_state()`, `load_state()`
- **Personality**: `detect_user_mood()`, `update_favorite_topics()`, `remember_emotional_context()`, `evolve_personality()`
- **Response Generation**: `handle_command()` and the optional Ollama branch
- **Command Handling**: `handle_command()` (main command dispatcher)

### Running Tests
Run the focused test suite with the project virtual environment:
```powershell
.venv\Scripts\python.exe -m pytest -q
```

The tests cover safe math evaluation, mood detection, greetings, memory updates,
and representative engaging commands. Manual testing is still recommended for
state persistence and optional integrations such as Ollama and GPU sensors.

## License

MIT License - feel free to use and modify

## Notes

- The assistant learns lightweight preferences from explicit conversation and memory entries
- Relationship level and companion mode are stored as personalization settings
- State file is JSON and can be edited manually if needed
