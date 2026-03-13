import os
import sys
import warnings

warnings.filterwarnings(
    "ignore",
    message="Pydantic serializer warnings",
    category=UserWarning,
    module="pydantic",
)

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY not set.")
    print("  Create a .env file in this directory with:")
    print("  OPENAI_API_KEY=sk-...")
    sys.exit(1)

from actors import run_actor
from referee import run_referee
from state import append_memory, apply_stance_changes, get_initial_state, get_memory_window

_DEBUG = os.getenv("CHAT_DEBUG", "").lower() == "true"


def print_debug_state(state: dict) -> None:
    npcs = state["npcs"]
    mara = npcs["gatekeeper"]["stance"]
    bram = npcs["opposer"]["stance"]
    print(f"  [debug] Mara — trust:{mara['trust']} fear:{mara['fear']} annoyance:{mara['annoyance']}")
    print(f"  [debug] Bram  — suspicion:{bram['suspicion']} aggression:{bram['aggression']}")

DIVIDER = "=" * 60
THIN = "-" * 60


def print_scene_header(scene: dict) -> None:
    print()
    print(DIVIDER)
    print(f"  {scene['title'].upper()}")
    print(DIVIDER)
    print(scene["description"])
    print(THIN)


def print_turn_header(turn: int, max_turns: int) -> None:
    print(f"\n[TURN {turn}/{max_turns}]")
    print(THIN)


def print_npc_speech(npc_name: str, speech: str) -> None:
    print(f"\n  [{npc_name.upper()}]")
    print(f"  \"{speech}\"")


def print_win() -> None:
    print()
    print(DIVIDER)
    print("  YOU HAVE LEARNED THE TRUTH.")
    print(DIVIDER)


def print_loss() -> None:
    print()
    print(DIVIDER)
    print("  YOU HAVE BEEN REMOVED FROM THE PREMISES.")
    print(DIVIDER)


def print_turn_limit() -> None:
    print()
    print(DIVIDER)
    print("  TIME HAS RUN OUT. THEY WAIT YOU OUT.")
    print(DIVIDER)


def main() -> None:
    state = get_initial_state()

    print_scene_header(state["scene"])
    print(f"  OBJECTIVE: {state['player']['goal']}")
    print(THIN)
    print("  Type your action or words. Press Ctrl+C to quit.")

    while True:
        turn = state["mechanics"]["turn"]
        max_turns = state["mechanics"]["max_turns"]

        if turn > max_turns:
            print_turn_limit()
            break

        print_turn_header(turn, max_turns)

        try:
            player_message = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nFarewell.")
            break

        if not player_message:
            continue

        print()
        print("  [ thinking... ]")

        # Step A: Referee
        referee_result = run_referee(state, player_message)

        # Step C (partial): merge referee output into state
        apply_stance_changes(state, referee_result["stance_changes"])

        mara = state["npcs"]["gatekeeper"]["stance"]
        bram = state["npcs"]["opposer"]["stance"]
        reveal_triggered = (mara["trust"] + mara["fear"]) >= 3
        kick_triggered = (bram["suspicion"] + bram["aggression"]) >= 4

        state["npcs"]["gatekeeper"]["allowed_to_reveal"] = referee_result["allowed_to_reveal"] or reveal_triggered
        state["mechanics"]["win_condition"]["player_has_truth"] = referee_result["win_update"]
        state["mechanics"]["loss_condition"]["kicked_out"] = referee_result["loss_update"] or kick_triggered

        if _DEBUG:
            print_debug_state(state)

        append_memory(state, f"Turn {turn}: Player: {player_message}")
        append_memory(state, f"Turn {turn}: Intent: {referee_result['player_intent']}")

        # Step B: NPC actors
        memory_window = get_memory_window(state)

        for npc_key in referee_result["npcs_speaking"]:
            npc_data = state["npcs"][npc_key]
            allowed = referee_result["allowed_to_reveal"] if npc_key == "gatekeeper" else False
            actor_result = run_actor(
                npc_key=npc_key,
                npc_data=npc_data,
                scene=state["scene"],
                memory_window=memory_window,
                player_intent=referee_result["player_intent"],
                allowed_to_reveal=allowed,
                ejecting=kick_triggered and npc_key == "opposer",
            )
            print_npc_speech(npc_data["name"], actor_result["speech"])
            append_memory(state, f"Turn {turn}: {npc_data['name']} [{actor_result['intent']}]: {actor_result['speech']}")

        if not referee_result["npcs_speaking"]:
            print("\n  Silence hangs in the room.")

        # Step C (final): check win/loss
        if state["mechanics"]["win_condition"]["player_has_truth"]:
            print_win()
            break

        if state["mechanics"]["loss_condition"]["kicked_out"]:
            print_loss()
            break

        state["mechanics"]["turn"] += 1


if __name__ == "__main__":
    main()
