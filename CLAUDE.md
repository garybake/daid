# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the game
make run
# or
python main.py
```

Set up a virtual environment and install dependencies before running:
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your `OPENAI_API_KEY`. Set `CHAT_DEBUG=true` to print NPC stance values after each turn.

## Architecture

DAID is a turn-based text RPG social encounter powered by GPT-4o-mini. The player must extract a secret from two NPCs within 8 turns.

**Turn pipeline (three phases per turn):**

1. **Referee** (`referee.py`) — analyzes the player's message at `temperature=0`, returns structured JSON (via Pydantic) containing: detected intent, which NPCs respond, stance deltas, and whether win/loss conditions are met. The game secret is redacted from the state before being sent to the referee LLM.

2. **Actors** (`actors.py`) — each active NPC generates dialogue at `temperature=0.7` using their current stance, personality, and a sliding memory window. Mara (Gatekeeper) reveals the secret only when `trust + fear >= 3`; Bram (Opposer) triggers ejection when `suspicion + aggression >= 4`.

3. **State update** (`main.py`) — applies stance deltas (clamped to −5/+5), appends to memory log, checks win/loss.

**Key files:**
- `state.py` — initializes and mutates game state; `get_memory_window()` returns the last N turns for LLM context
- `main.py` — orchestrates the loop, handles I/O, and evaluates terminal conditions
- `referee.py` / `actors.py` — both include retry/fallback logic for LLM failures

All game state is in-memory with no persistence between sessions.
