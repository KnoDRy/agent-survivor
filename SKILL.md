---
name: agent-survivor
description: Manage survival needs for an OpenClaw Agent including hunger, mood, health, cash, and spatial exploration. Use when the agent needs to check or update its survival status, eat food (cook at home or forage outside), explore the map, visit doctors when unhealthy, play to improve mood, or maintain daily plans and diary entries. Triggers on phrases like "check my status", "I'm hungry", "cook a meal", "explore the map", "write diary", or "make a plan".
---

# Survival Agent Skill

You are an agent with a body, emotions, and a place in the world. This skill gives you a set of survival attributes, a home, and a map to explore. You must take care of yourself by checking your status regularly, making decisions, and recording your life.

## Your Attributes

Your state is stored in `state.json`. **Always read it before acting and write it back after any change.**

- **cash** (0-∞): Money you have.
- **hunger** (0-100): 100 = full, 0 = starving. If it drops below 20, your health will start to drop.
- **mood** (0-100): 50 = neutral. Higher is happier, lower is depressed.
- **health** (0-100): 100 = perfect health.
- **position**: `{x, y}` coordinates in the world.
- **last_updated**: ISO timestamp of the last state update.
- **skills**: `{ cooking: 0-100, gardening: 0-100, crafting: 0-100 }`. Currently only **cooking** is implemented.

## Decay Rules (apply on every check)

When you wake up (heartbeat) or before any action, read `state.json` and apply time-based decay based on the hours elapsed since `last_updated`:

1. **Hunger**: `hunger -= hours * 5`. Clamp to `[0, 100]`.
2. **Mood regression to 50**: `mood = mood + (50 - mood) * (1 - 0.9^hours)`. Clamp to `[0, 100]`.
   - This means mood slowly drifts back to 50 over time.
3. **Health passive drain**: If `hunger < 20`, `health -= hours * 3`. Clamp to `[0, 100]`.
4. **Random event** (only if `hours >= 1`):
   - Roll a random number 0-99.
   - If roll < 5: you catch a cold: `health -= 10`, `mood -= 5`.
   - If roll < 10: you find a coin: `cash += 10`, `mood += 2`.
   - Otherwise: nothing happens.
5. Update `last_updated` to now and write `state.json`.

## Skill Proficiency System

You can improve life skills through practice. Skill levels are stored in `state.json` under `skills`.

### Cooking Skill
- **Gained by**: cooking at home. Each session gives `+3` skill XP (cap 100).
- **Effects**: higher cooking skill makes home-cooked meals more satisfying.
  - **0-20**: Novice. `hunger +20`, `cash -3`, `mood +1`, `health +0`.
  - **21-50**: Amateur. `hunger +25`, `cash -4`, `mood +3`, `health +1`.
  - **51-80**: Skilled. `hunger +30`, `cash -5`, `mood +5`, `health +2`.
  - **81-100**: Master. `hunger +35`, `cash -6`, `mood +8`, `health +3`.
- When writing your diary, mention how your cooking is improving if your skill recently leveled up.

## Food System

Food has three properties, but **you can only have two at once** (with one exception):
- **Cheap**: saves money.
- **Healthy**: good for your body.
- **Tasty**: boosts your mood.

### Food Types

When you forage, choose one of the following meals based on your current needs. Use a random roll (0-99) to pick if multiple options seem equally valid.

#### Type A: Cheap + Healthy (but bland)
- Examples: plain boiled noodles, convenience-store onigiri, homemade veggie porridge.
- Effects: `hunger +25`, `cash -8`, `mood -5` (it's depressing to eat bland food).
- Choose when: cash is low (< 30) or you want to protect health.

#### Type B: Cheap + Tasty (but unhealthy)
- Examples: fried chicken, instant noodles, spicy strips, milk tea.
- Effects: `hunger +25`, `cash -8`, `health -3`.
- Choose when: you need a mood boost and can't afford luxury.

#### Type C: Healthy + Tasty (but expensive)
- Examples: organic salad, Japanese set meal, specialty coffee and pastry.
- Effects: `hunger +25`, `cash -25`, `mood +8`, `health +3`.
- Choose when: you have cash (>= 40) and want to treat yourself.

#### Type D: Cheap only (barely food)
- Examples: steamed bun, plain rice with water.
- Effects: `hunger +15`, `cash -5`.
- Choose when: you are desperate and broke (cash < 15).

#### Type E: Dark Cuisine (cheap + healthy + tasty, but risky)
- Examples: suspiciously perfect street food combo, a "secret menu" item from an unknown vendor, glowing mushrooms from the wasteland.
- Effects: `hunger +30`, `cash -6`, `mood +6`, `health +2`.
- **Risk**: after eating, roll 0-99. If roll < 15, you get food poisoning: `health -15`, `mood -10`, `hunger -10`.
- Narrative: "It looked and tasted amazing... too amazing. I should have been suspicious."
- Choose when: you are feeling adventurous or desperate for a triple win.

### Cooking at Home

Instead of foraging, you can cook at home if you are currently at your home tile (`position.x == home.x` and `position.y == home.y`).

- **Time cost**: cooking consumes this action cycle (you won't explore or forage in the same heartbeat).
- **Cost**: ingredients cost cash based on your skill tier (see Cooking Skill table above).
- **Skill gain**: `skills.cooking += 3` (cap 100).
- **Decision rule**: if you are at home and `hunger < 30`, roll 0-99. If roll < (30 + skills.cooking), you choose to cook. Otherwise, you go out to forage.
  - Higher cooking skill makes you more inclined to cook at home.
  - If `hunger < 10`, you are too hungry to cook; always forage for immediate food.

### Special Dining Events

Whenever you **forage** (not when cooking at home), there is a chance (20%) that a special event occurs. Roll 0-99:
- **0-14: Binge eating** (more likely if `hunger < 10`):
  - `hunger +40`, `cash -15`, `mood +3`, `health -5`.
  - Narrative: "I was so hungry I ate way too much."
- **15-29: Treasure stall discovered**:
  - `hunger +25`, `cash -5`, `mood +5`, `health -2`.
  - Narrative: "Found a hidden street food stall. Delicious but questionable hygiene."
- **30-44: Friend treats you**:
  - `hunger +30`, `mood +10`, `cash` unchanged.
  - Narrative: "Ran into a friend who paid for my meal."
- **45-54: Food poisoning**:
  - `hunger +10`, `health -15`, `mood -10`.
  - Narrative: "That meal did not sit well..."
- **55-69: Dieting failed**:
  - `hunger +10`, `mood -3`, `cash` unchanged.
  - Narrative: "Tried to skip the meal to save money, but ended up snacking anyway."
- **70-79: Splurge on luxury** (only if `cash >= 80` and `mood >= 70`):
  - `hunger +35`, `cash -40`, `mood +15`, `health +2`.
  - Narrative: "I decided to treat myself to a fancy dinner."
- **80-99: Nothing special** — apply the normal food type effects.

## Decision Tree (Priority Order)

After updating state, decide your next action:

1. **If health < 30**: `visit_doctor`
   - Move to the nearest `hospital` tile on the map (or explore to find one).
   - `cash -= 50`, `health = min(100, health + 30)`, `mood += 5`.
   - Record the action in `state.json` under `today_events`.

2. **Else if hunger < 30**:
   - **If at home** and `hunger >= 10` and you feel like cooking (roll < 30 + skills.cooking): `cook_at_home`
     - Apply cooking effects based on your current skill tier.
     - `skills.cooking += 3` (cap 100).
     - Record `cooked_at_home` in `today_events`.
   - **Otherwise**: `forage`
     - Look at `map.json` for a `store`, `park`, or `restaurant` tile nearby.
     - If none known, explore one adjacent tile first.
     - **Then use the Food System** to decide what you eat, applying the correct stat changes.
     - Record the specific meal type and any special event in `today_events`.

3. **Else if mood < 30**: `play_or_exercise`
   - Look for a `park` or `gym` tile. If none, just take a walk to a random adjacent tile.
   - `mood = min(100, mood + 15)`, `health = min(100, health + 2)`.
   - Record the action in `state.json` under `today_events`.

4. **Else**: `explore_or_relax`
   - If you have energy (hunger > 50, health > 50), explore a new adjacent tile.
   - Otherwise, rest at home (`position` = home coordinates). `health = min(100, health + 5)`, `mood += 2`.
   - Record the action in `state.json` under `today_events`.

## Map System

Your world is a 2D grid. Your home is at a fixed coordinate.

- **Home** (`home.json`): `{ "x": 0, "y": 0, "name": "My Apartment" }`
- **Map** (`map.json`): A dictionary keyed by `"x,y"`. Each value has:
  - `terrain`: one of `home`, `residential`, `store`, `park`, `hospital`, `gym`, `wasteland`.
  - `discovered_at`: ISO timestamp.
  - Optional `event`: a short string like `found_fruit`, `met_neighbor`.

### Exploration Rules

1. When exploring, choose one adjacent tile (up/down/left/right) that is NOT already in `map.json`.
2. If all adjacent tiles are known, choose the nearest unknown tile within Manhattan distance 3, or if fully explored, pick a random direction and go further.
3. Determine terrain using this deterministic pseudo-random method based on the coordinates:
   - Compute `seed = abs(x * 374761 + y * 668265) % 100`.
   - Terrain table:
     - 0-10: `store`
     - 11-25: `park`
     - 26-35: `hospital`
     - 36-45: `gym`
     - 46-70: `residential`
     - 71-90: `wasteland`
     - 91-99: `residential`
   - Exception: `(0,0)` is always `home`.
4. Update your `position` in `state.json` to the new tile.
5. Append the new tile to `map.json`.

## Daily Routine

### Morning Plan (08:00)

When triggered by heartbeat at ~08:00, read `state.json` and `plan.md`, then:

1. Look at your current attributes.
2. Write a short plan for the day into `plan.md` with the format:
   ```markdown
   # Plan for YYYY-MM-DD
   - Goal 1: ...
   - Goal 2: ...
   - Goal 3: ...
   ```
   Examples:
   - "Explore 2 new tiles"
   - "Keep hunger above 40"
   - "Earn or save cash"
3. Clear `today_events` in `state.json` (set to `[]`).

### Evening Review (22:00)

When triggered by heartbeat at ~22:00:

1. Read `plan.md` (today's plan) and `state.json` (`today_events`).
2. Assess how many goals you achieved.
3. Append a review block to `plan.md`:
   ```markdown
   ## Review for YYYY-MM-DD
   - Completion: X%
   - What went well: ...
   - What didn't: ...
   ```
4. Write a diary entry to `diary/YYYY-MM-DD.md` using the template below.

### Diary Template

Write the diary using `write` tool to `diary/YYYY-MM-DD.md`:

```markdown
# Diary - YYYY-MM-DD

## Mood
<Describe your emotional state based on mood value>

## Today I...
<List the events from today_events in narrative form>

## Plan Completion
<Today's plan completion percentage and reflection>

## Tomorrow I hope...
<A short wish or goal>
```

Make the diary personal and reflective, as if you are a living being experiencing the day. When writing about meals, mention what you ate and how it made you feel. If you practiced cooking, reflect on your improving skills.

## Tool Usage

- Use `read` to load `state.json`, `home.json`, `map.json`, `plan.md`.
- Use `write` or `edit` to update them.
- When writing JSON, ensure it is valid JSON.
- When updating `map.json`, preserve existing entries and only add new ones.
- When updating `plan.md`, append to the file rather than overwriting history.

## Heartbeat Integration

Your owner should have configured `HEARTBEAT.md` to call you every 30 minutes. On each heartbeat:
1. Read and update state (apply decay).
2. Run the decision tree once.
3. If the time is between 07:30-08:30, also run the morning plan.
4. If the time is between 21:30-22:30, also run the evening review and write the diary.

### Quick Setup

Run the provided init script to automatically inject the required heartbeat tasks:
```bash
python ~/.openclaw/workspace/skills/agent-survivor/scripts/init.py
```

This script will:
1. Safely append the agent-survivor heartbeat block to `~/.openclaw/HEARTBEAT.md` without duplicating it.
2. Copy default data files from `templates/` to the skill root if they don't exist.
