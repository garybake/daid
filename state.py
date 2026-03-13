import copy


def get_initial_state() -> dict:
    return copy.deepcopy({
        "scene": {
            "title": "Backroom of the Lantern Inn",
            "premise": "Player needs the location of the hidden ledger.",
            "description": "A smoky backroom. A locked cabinet. Two people watching you.",
        },
        "player": {
            "name": "Player",
            "goal": "Learn where the hidden ledger is.",
            "approach_notes": "",
        },
        "npcs": {
            "gatekeeper": {
                "name": "Mara the Clerk",
                "role": "Has the true info",
                "goal": "Protect herself; only reveal info if safe/beneficial",
                "stance": {"trust": 0, "fear": 0, "annoyance": 0},
                "secret_truth": "The ledger is in the chapel crypt behind the third stone.",
                "allowed_to_reveal": False,
            },
            "opposer": {
                "name": "Bram the Enforcer",
                "role": "Blocks or redirects",
                "goal": "Prevent the player getting the truth; keep control",
                "stance": {"suspicion": 1, "aggression": 0},
                "tactics": ["intimidate", "redirect", "lie-plausibly"],
            },
        },
        "mechanics": {
            "turn": 1,
            "max_turns": 8,
            "win_condition": {"player_has_truth": False},
            "loss_condition": {"kicked_out": False},
            "checks": {"persuasion_threshold": 3, "deception_threshold": 3},
        },
        "memory_log": ["Scene starts. Player enters."],
    })


def get_memory_window(state: dict, n: int = 4) -> str:
    return "\n".join(state["memory_log"][-n:])


def apply_stance_changes(state: dict, changes: dict) -> None:
    for npc_key, deltas in changes.items():
        if npc_key not in state["npcs"]:
            continue
        stance = state["npcs"][npc_key]["stance"]
        for attr, delta in deltas.items():
            if attr in stance:
                stance[attr] = max(-5, min(5, stance[attr] + delta))


def append_memory(state: dict, entry: str) -> None:
    state["memory_log"].append(entry)
