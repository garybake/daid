import copy
import json
import time
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


class _GatekeeperStance(BaseModel):
    trust: int
    fear: int
    annoyance: int


class _OpposerStance(BaseModel):
    suspicion: int
    aggression: int


class _StanceChanges(BaseModel):
    gatekeeper: _GatekeeperStance
    opposer: _OpposerStance


class RefereeResponse(BaseModel):
    npcs_speaking: list[Literal["gatekeeper", "opposer"]]
    allowed_to_reveal: bool
    stance_changes: _StanceChanges
    player_intent: str
    win_update: bool
    loss_update: bool

_SYSTEM = """\
You are the Referee for a tabletop RPG social encounter.
You receive the current game state and the player's latest message.
Your job is to determine what happens next according to the game rules.

GAME RULES:
- Gatekeeper (Mara) reveals the truth when her trust + fear >= 3.
- Opposer (Bram) ejects the player when his suspicion + aggression >= 4.
- NPCs speak in the order listed in npcs_speaking.
- Bram (opposer) speaks in most turns; he is watchful and interventionist. Omit him only if the player is clearly having a private moment with Mara alone.
- Mara (gatekeeper) speaks in most turns. Omit her only if Bram is doing all the talking and she has nothing to add.
- Stance change values must be integers between -2 and +2.
- Set win_update to true only if the memory log shows Mara has already disclosed the secret location to the player.
- allowed_to_reveal unlocks Mara's ability to speak the truth; win_update confirms she has actually done so.

STANCE CHANGE GUIDELINES:
- polite/empathic approach: gatekeeper trust +1, opposer suspicion +0
- bribe attempt: gatekeeper trust +1, opposer suspicion +1
- threat: gatekeeper fear +1, opposer aggression +1
- obvious lie: opposer suspicion +2
- direct question: no stance change
- backing off/apologising: opposer aggression -1

CURRENT STATE:
{state_json}

PLAYER MESSAGE:
{player_message}

"""

_HUMAN = "Assess the player's message and return the referee JSON."

_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM),
    ("human", _HUMAN),
])

_chain = _prompt | _llm.with_structured_output(RefereeResponse, method="json_schema", strict=True)

_MAX_RETRIES = 2


def _sanitize_state(state: dict) -> dict:
    sanitized = copy.deepcopy(state)
    sanitized["npcs"]["gatekeeper"]["secret_truth"] = "[REDACTED - only revealed when allowed_to_reveal is true]"
    return sanitized


def _validate(result: RefereeResponse) -> dict:
    return result.model_dump()


def _fallback() -> dict:
    return {
        "npcs_speaking": [],
        "allowed_to_reveal": False,
        "stance_changes": {"gatekeeper": {"trust": 0, "fear": 0, "annoyance": 0}, "opposer": {"suspicion": 0, "aggression": 0}},
        "player_intent": "unknown",
        "win_update": False,
        "loss_update": False,
    }


def run_referee(state: dict, player_message: str) -> dict:
    state_json = json.dumps(_sanitize_state(state), indent=2)
    for attempt in range(_MAX_RETRIES + 1):
        try:
            result = _chain.invoke({"state_json": state_json, "player_message": player_message})
            return _validate(result)
        except Exception as e:
            print(f"  [referee error attempt {attempt}]: {e}")
            if attempt == _MAX_RETRIES:
                return _fallback()
            time.sleep(1)
    return _fallback()
