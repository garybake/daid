# DAID

A turn-based text RPG social encounter powered by GPT-4o-mini. You have 8 turns to extract a secret from two NPCs at the Lantern Inn — a protective clerk and an enforcer who wants you gone.

## Setup

```bash
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-...
```

## Running

```bash
make run
# or
python main.py
```

## How to Play

Type your character's words or actions at each `>` prompt. The two NPCs — **Mara** (the clerk) and **Bram** (the enforcer) — will respond based on how you approach them.

**Win:** Get Mara to reveal the secret location.
**Lose:** Push Bram too far and get thrown out, or run out of turns.

## Debug Mode

Set `CHAT_DEBUG=true` in `.env` to print each NPC's stance values after every turn.
