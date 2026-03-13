import time
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)


class ActorResponse(BaseModel):
    speech: str
    intent: Literal["stall", "probe", "intimidate", "bargain", "disclose", "lie", "deflect"]

_SYSTEM = """\
You are roleplaying as {npc_name}, a character in a tabletop RPG encounter.

YOUR CHARACTER:
- Role: {npc_role}
- Goal: {npc_goal}
- Current stance: {npc_stance}
{extra_lines}
SCENE: {scene_title}
{scene_description}

RECENT EVENTS:
{memory_window}

Stay in character. Be concise (1-4 sentences). Speak naturally, not like a game description.\
"""

_HUMAN = """\
The player's intent is: {player_intent}
{reveal_instruction}\
"""

_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM),
    ("human", _HUMAN),
])

_chain = _prompt | _llm.with_structured_output(ActorResponse, method="json_schema", strict=True)
_MAX_RETRIES = 2


def _fallback(npc_name: str) -> dict:
    return {"speech": f"{npc_name} watches you in silence.", "intent": "stall"}


def run_actor(
    npc_key: str,
    npc_data: dict,
    scene: dict,
    memory_window: str,
    player_intent: str,
    allowed_to_reveal: bool,
    ejecting: bool = False,
) -> dict:
    extra_lines = ""

    if npc_key == "gatekeeper":
        if allowed_to_reveal:
            secret = npc_data.get("secret_truth", "")
            extra_lines += f"- Secret you may now reveal: {secret}\n"
        else:
            extra_lines += "- You have a secret but will NOT reveal it under any circumstances yet.\n"

    if npc_key == "opposer":
        tactics = npc_data.get("tactics", [])
        extra_lines += f"- Available tactics: {', '.join(tactics)}\n"
        if ejecting:
            extra_lines += "- You have had enough. You are throwing the player out. Make it explicit and final.\n"

    if allowed_to_reveal and npc_key == "gatekeeper":
        reveal_instruction = "You may reveal your secret truth now if it feels natural to your character."
    else:
        reveal_instruction = "Do NOT reveal any secret information."

    for attempt in range(_MAX_RETRIES + 1):
        try:
            result = _chain.invoke({
                "npc_name": npc_data["name"],
                "npc_role": npc_data["role"],
                "npc_goal": npc_data["goal"],
                "npc_stance": str(npc_data["stance"]),
                "extra_lines": extra_lines,
                "scene_title": scene["title"],
                "scene_description": scene["description"],
                "memory_window": memory_window,
                "player_intent": player_intent,
                "reveal_instruction": reveal_instruction,
            })
            return result.model_dump()
        except Exception:
            if attempt == _MAX_RETRIES:
                return _fallback(npc_data["name"])
            time.sleep(1)
    return _fallback(npc_data["name"])
