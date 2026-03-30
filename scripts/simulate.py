#!/usr/bin/env python3
"""
Local simulation script for the survival-agent skill.
This simulates time passing and state decay so you can verify the math
without installing OpenClaw.
"""

import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Paths to data files (in parent directory, skill root)
SKILL_ROOT = Path(__file__).parent.parent
STATE_PATH = SKILL_ROOT / "state.json"
MAP_PATH = SKILL_ROOT / "map.json"
HOME_PATH = SKILL_ROOT / "home.json"


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def terrain_for(x: int, y: int) -> str:
    if x == 0 and y == 0:
        return "home"
    seed = abs(x * 374761 + y * 668265) % 100
    if seed <= 10:
        return "store"
    if seed <= 25:
        return "park"
    if seed <= 35:
        return "hospital"
    if seed <= 45:
        return "gym"
    if seed <= 70:
        return "residential"
    if seed <= 90:
        return "wasteland"
    return "residential"


def apply_decay(state: dict, hours: float):
    """Apply the same decay rules described in SKILL.md."""
    state["hunger"] = max(0, min(100, state["hunger"] - hours * 5))

    # Mood regression to 50
    mood = state["mood"]
    state["mood"] = max(0, min(100, mood + (50 - mood) * (1 - math.pow(0.9, hours))))

    # Health drain from starvation
    if state["hunger"] < 20:
        state["health"] = max(0, state["health"] - hours * 3)

    # Random events (only if at least 1 hour passed)
    if hours >= 1:
        roll = random.randint(0, 99)
        if roll < 5:
            state["health"] = max(0, state["health"] - 10)
            state["mood"] = max(0, state["mood"] - 5)
            print("  [EVENT] Caught a cold!")
        elif roll < 10:
            state["cash"] += 10
            state["mood"] = min(100, state["mood"] + 2)
            print("  [EVENT] Found a coin!")

    state["health"] = max(0, min(100, state["health"]))
    state["mood"] = max(0, min(100, state["mood"]))


def explore(state: dict, map_data: dict):
    """Explore one new adjacent tile."""
    x, y = state["position"]["x"], state["position"]["y"]
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    random.shuffle(directions)

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        key = f"{nx},{ny}"
        if key not in map_data:
            map_data[key] = {
                "terrain": terrain_for(nx, ny),
                "discovered_at": datetime.now(timezone.utc).isoformat(),
            }
            state["position"] = {"x": nx, "y": ny}
            print(f"  [EXPLORE] Moved to ({nx}, {ny}) -> {map_data[key]['terrain']}")
            return

    # All adjacent known -> pick random direction anyway
    dx, dy = directions[0]
    nx, ny = x + dx, y + dy
    state["position"] = {"x": nx, "y": ny}
    print(f"  [WALK] Moved to ({nx}, {ny})")


def get_cooking_tier(skill: int) -> int:
    if skill >= 81:
        return 4
    if skill >= 51:
        return 3
    if skill >= 21:
        return 2
    return 1


def cook_at_home(state: dict):
    """Cook a meal at home."""
    events = state.setdefault("today_events", [])
    skill = state.get("skills", {}).get("cooking", 0)
    tier = get_cooking_tier(skill)

    if tier == 1:
        state["hunger"] = min(100, state["hunger"] + 20)
        state["cash"] -= 3
        state["mood"] = min(100, state["mood"] + 1)
        print(f"  [COOK] Cooked a novice meal (skill={skill})")
    elif tier == 2:
        state["hunger"] = min(100, state["hunger"] + 25)
        state["cash"] -= 4
        state["mood"] = min(100, state["mood"] + 3)
        state["health"] = min(100, state["health"] + 1)
        print(f"  [COOK] Cooked an amateur meal (skill={skill})")
    elif tier == 3:
        state["hunger"] = min(100, state["hunger"] + 30)
        state["cash"] -= 5
        state["mood"] = min(100, state["mood"] + 5)
        state["health"] = min(100, state["health"] + 2)
        print(f"  [COOK] Cooked a skilled meal (skill={skill})")
    else:
        state["hunger"] = min(100, state["hunger"] + 35)
        state["cash"] -= 6
        state["mood"] = min(100, state["mood"] + 8)
        state["health"] = min(100, state["health"] + 3)
        print(f"  [COOK] Cooked a master meal (skill={skill})")

    # Gain skill
    state.setdefault("skills", {})["cooking"] = min(100, skill + 3)
    events.append("cooked_at_home")


def choose_food_type(state: dict) -> str:
    """Choose a food type based on current stats."""
    cash = state["cash"]
    health = state["health"]
    mood = state["mood"]

    if cash < 15:
        return "D"
    if cash < 30:
        # Broke: prefer A or D
        return random.choice(["A", "A", "D"])
    if health < 40:
        # Need health: prefer A or C
        return random.choice(["A", "C", "C"])
    if mood < 40:
        # Need mood: prefer B or C
        return random.choice(["B", "C", "C"])
    if cash >= 80 and mood >= 70:
        # Feeling good and rich: might splurge or try dark cuisine
        return random.choice(["C", "C", "B", "A", "E"])
    # Default balanced, with small chance of dark cuisine
    return random.choice(["A", "B", "C", "E"])


def apply_food_effects(state: dict, food_type: str, event_name: Optional[str]):
    """Apply normal or special dining effects."""
    if event_name == "binge":
        state["hunger"] = min(100, state["hunger"] + 40)
        state["cash"] -= 15
        state["mood"] = min(100, state["mood"] + 3)
        state["health"] = max(0, state["health"] - 5)
        print("  [FOOD EVENT] Binge eating!")
    elif event_name == "treasure_stall":
        state["hunger"] = min(100, state["hunger"] + 25)
        state["cash"] -= 5
        state["mood"] = min(100, state["mood"] + 5)
        state["health"] = max(0, state["health"] - 2)
        print("  [FOOD EVENT] Discovered a treasure street stall!")
    elif event_name == "friend_treat":
        state["hunger"] = min(100, state["hunger"] + 30)
        state["mood"] = min(100, state["mood"] + 10)
        print("  [FOOD EVENT] A friend treated me!")
    elif event_name == "food_poisoning":
        state["hunger"] = min(100, state["hunger"] + 10)
        state["health"] = max(0, state["health"] - 15)
        state["mood"] = max(0, state["mood"] - 10)
        print("  [FOOD EVENT] Food poisoning...")
    elif event_name == "diet_fail":
        state["hunger"] = min(100, state["hunger"] + 10)
        state["mood"] = max(0, state["mood"] - 3)
        print("  [FOOD EVENT] Dieting failed, ended up snacking.")
    elif event_name == "luxury_splurge":
        state["hunger"] = min(100, state["hunger"] + 35)
        state["cash"] -= 40
        state["mood"] = min(100, state["mood"] + 15)
        state["health"] = min(100, state["health"] + 2)
        print("  [FOOD EVENT] Splurged on a luxury dinner!")
    else:
        # Normal food type effects
        if food_type == "A":
            state["hunger"] = min(100, state["hunger"] + 25)
            state["cash"] -= 8
            state["mood"] = max(0, state["mood"] - 5)
            print("  [MEAL] Ate cheap healthy food (bland)")
        elif food_type == "B":
            state["hunger"] = min(100, state["hunger"] + 25)
            state["cash"] -= 8
            state["health"] = max(0, state["health"] - 3)
            print("  [MEAL] Ate cheap tasty junk food")
        elif food_type == "C":
            state["hunger"] = min(100, state["hunger"] + 25)
            state["cash"] -= 25
            state["mood"] = min(100, state["mood"] + 8)
            state["health"] = min(100, state["health"] + 3)
            print("  [MEAL] Ate expensive healthy tasty food")
        elif food_type == "D":
            state["hunger"] = min(100, state["hunger"] + 15)
            state["cash"] -= 5
            print("  [MEAL] Ate the bare minimum")
        elif food_type == "E":
            # Dark cuisine: triple win but risky
            state["hunger"] = min(100, state["hunger"] + 30)
            state["cash"] -= 6
            state["mood"] = min(100, state["mood"] + 6)
            state["health"] = min(100, state["health"] + 2)
            print("  [MEAL] Ate dark cuisine (suspiciously perfect)")
            # 15% chance of poisoning
            if random.randint(0, 99) < 15:
                state["health"] = max(0, state["health"] - 15)
                state["mood"] = max(0, state["mood"] - 10)
                state["hunger"] = max(0, state["hunger"] - 10)
                print("  [DARK CUISINE] Food poisoning! It was too good to be true...")


def resolve_special_event(state: dict) -> Optional[str]:
    """Roll for a special dining event. Returns event name or None."""
    roll = random.randint(0, 99)
    if roll <= 14:
        # Binge eating — more likely if very hungry
        if state["hunger"] < 10 or random.random() < 0.5:
            return "binge"
        return None
    elif roll <= 29:
        return "treasure_stall"
    elif roll <= 44:
        return "friend_treat"
    elif roll <= 54:
        return "food_poisoning"
    elif roll <= 69:
        return "diet_fail"
    elif roll <= 79:
        if state["cash"] >= 80 and state["mood"] >= 70:
            return "luxury_splurge"
        return None
    else:
        return None


def forage(state: dict, map_data: dict):
    """Find food and eat."""
    events = state.setdefault("today_events", [])

    food_tile = next(
        (k for k, v in map_data.items() if v["terrain"] in ("store", "park", "restaurant")),
        None,
    )
    if food_tile:
        x, y = map(int, food_tile.split(","))
        state["position"] = {"x": x, "y": y}
        print(f"  [FORAGE] Found food spot at ({x}, {y}) -> {map_data[food_tile]['terrain']}")
    else:
        explore(state, map_data)
        print("  [FORAGE] Looking for food...")
        return

    food_type = choose_food_type(state)
    event = resolve_special_event(state)
    apply_food_effects(state, food_type, event)

    event_label = event if event else f"meal_{food_type}"
    events.append(f"foraged:{event_label}")


def decide_and_act(state: dict, map_data: dict):
    """Run the decision tree once."""
    events = state.setdefault("today_events", [])
    home = load_json(HOME_PATH)
    at_home = state["position"]["x"] == home["x"] and state["position"]["y"] == home["y"]

    if state["health"] < 30:
        # Find nearest hospital or explore
        hospital = next(
            (k for k, v in map_data.items() if v["terrain"] == "hospital"), None
        )
        if hospital:
            x, y = map(int, hospital.split(","))
            state["position"] = {"x": x, "y": y}
            print(f"  [DOCTOR] Visited hospital at ({x}, {y})")
        else:
            explore(state, map_data)
            print("  [DOCTOR] Looking for hospital...")
            return
        state["cash"] -= 50
        state["health"] = min(100, state["health"] + 30)
        state["mood"] = min(100, state["mood"] + 5)
        events.append("visited_doctor")

    elif state["hunger"] < 30:
        cooking_skill = state.get("skills", {}).get("cooking", 0)
        # Decide whether to cook at home
        if at_home and state["hunger"] >= 10 and random.randint(0, 99) < (30 + cooking_skill):
            cook_at_home(state)
        else:
            forage(state, map_data)

    elif state["mood"] < 30:
        fun_tile = next(
            (k for k, v in map_data.items() if v["terrain"] in ("park", "gym")),
            None,
        )
        if fun_tile:
            x, y = map(int, fun_tile.split(","))
            state["position"] = {"x": x, "y": y}
            print(f"  [PLAY] Went to ({x}, {y}) -> {map_data[fun_tile]['terrain']}")
        else:
            explore(state, map_data)
            print("  [PLAY] Looking for fun...")
            return
        state["mood"] = min(100, state["mood"] + 15)
        state["health"] = min(100, state["health"] + 2)
        events.append("played")

    else:
        if state["hunger"] > 50 and state["health"] > 50:
            explore(state, map_data)
            events.append("explored")
        else:
            state["position"] = {"x": home["x"], "y": home["y"]}
            state["health"] = min(100, state["health"] + 5)
            state["mood"] = min(100, state["mood"] + 2)
            print("  [REST] Stayed home to rest")
            events.append("rested")


def simulate(hours: float = 2.0):
    state = load_json(STATE_PATH)
    map_data = load_json(MAP_PATH)

    last = datetime.fromisoformat(state["last_updated"])
    now = last + timedelta(hours=hours)

    skill_str = f", cooking={state.get('skills', {}).get('cooking', 0)}"
    print(f"Simulating {hours} hour(s) from {last.isoformat()} to {now.isoformat()}")
    print(f"  Before: cash={state['cash']}, hunger={state['hunger']:.1f}, mood={state['mood']:.1f}, health={state['health']:.1f}{skill_str}")

    apply_decay(state, hours)
    decide_and_act(state, map_data)

    state["last_updated"] = now.isoformat()
    skill_str = f", cooking={state.get('skills', {}).get('cooking', 0)}"
    print(f"  After:  cash={state['cash']}, hunger={state['hunger']:.1f}, mood={state['mood']:.1f}, health={state['health']:.1f}{skill_str}")
    print(f"  Events today: {state.get('today_events', [])}")
    print(f"  Position: ({state['position']['x']}, {state['position']['y']})")

    save_json(STATE_PATH, state)
    save_json(MAP_PATH, map_data)


if __name__ == "__main__":
    import sys
    hours = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    simulate(hours)
