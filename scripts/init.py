#!/usr/bin/env python3
"""
Survival Agent Skill Init Script

This script initializes the agent-survivor skill by:
1. Ensuring the skill directory is installed in the OpenClaw workspace.
2. Copying default data files from templates/ if they don't exist.
3. Injecting required heartbeat tasks into ~/.openclaw/HEARTBEAT.md (if not already present).

Run this after copying the agent-survivor directory to:
~/.openclaw/workspace/skills/agent-survivor/
"""

import os
import shutil
import sys
from pathlib import Path

# OpenClaw default paths
OPENCLAW_DIR = Path.home() / ".openclaw"
HEARTBEAT_PATH = OPENCLAW_DIR / "workspace" / "HEARTBEAT.md"
SKILL_TARGET = OPENCLAW_DIR / "workspace" / "skills" / "agent-survivor"

# Data files to copy from templates
DATA_FILES = ["state.json", "home.json", "map.json", "plan.md"]

SURVIVAL_HEARTBEAT_BLOCK = """\n<!-- BEGIN agent-survivor heartbeat -->
## Survival Agent Check (every 30 minutes)
- Read `~/.openclaw/workspace/skills/agent-survivor/state.json`.
- Apply decay rules based on elapsed time since `last_updated`.
- Run the survival decision tree once (cook / forage / play / doctor / explore / relax).
- Write updated state back.

## Survival Agent Morning Plan (08:00 daily)
- Read state and plan files.
- Write today's goals to `~/.openclaw/workspace/skills/agent-survivor/plan.md`.
- Clear `today_events` in state.

## Survival Agent Evening Review (22:00 daily)
- Assess plan completion and append review to plan.md.
- Write diary entry to `~/.openclaw/workspace/skills/agent-survivor/diary/YYYY-MM-DD.md`.
<!-- END agent-survivor heartbeat -->
"""


def get_skill_root():
    """Get the skill root directory (parent of scripts/)."""
    return Path(__file__).parent.parent.resolve()


def ensure_data_files(skill_dir: Path):
    """Copy default data files from templates/ if they don't exist."""
    templates_dir = skill_dir / "templates"
    if not templates_dir.exists():
        print(f"[WARN] Templates directory not found: {templates_dir}")
        return False

    copied = []
    for filename in DATA_FILES:
        target = skill_dir / filename
        source = templates_dir / f"{filename}.default"
        
        if not target.exists() and source.exists():
            shutil.copy2(source, target)
            copied.append(filename)
    
    if copied:
        print(f"[OK] Created default data files: {', '.join(copied)}")
    else:
        print(f"[OK] Data files already exist")
    
    # Ensure diary directory exists
    diary_dir = skill_dir / "diary"
    if not diary_dir.exists():
        diary_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created diary directory")
    
    return True


def ensure_skill_installed():
    """Check if the skill is in the OpenClaw workspace. If not, offer to copy it."""
    if SKILL_TARGET.exists():
        print(f"[OK] Skill already installed at: {SKILL_TARGET}")
        # Still ensure data files are present
        ensure_data_files(SKILL_TARGET)
        return True

    skill_root = get_skill_root()
    print(f"[WARN] Skill not found at expected location: {SKILL_TARGET}")
    print(f"[INFO] Current directory: {skill_root}")

    if skill_root.name == "agent-survivor":
        answer = input("Would you like to copy the current directory to the OpenClaw skills folder? [Y/n] ").strip().lower()
        if answer in ("", "y", "yes"):
            SKILL_TARGET.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(skill_root, SKILL_TARGET)
            print(f"[OK] Copied skill to: {SKILL_TARGET}")
            # Copy default data files
            ensure_data_files(SKILL_TARGET)
            return True
        else:
            print("[SKIP] Skill not copied. Please copy it manually.")
            return False
    else:
        print("[SKIP] Please copy the agent-survivor directory to:")
        print(f"       {SKILL_TARGET}")
        return False


def inject_heartbeat():
    """Inject agent-survivor tasks into HEARTBEAT.md if not already present."""
    if not HEARTBEAT_PATH.exists():
        print(f"[WARN] HEARTBEAT.md not found at: {HEARTBEAT_PATH}")
        create = input("Create a new HEARTBEAT.md with agent-survivor tasks? [Y/n] ").strip().lower()
        if create in ("", "y", "yes"):
            OPENCLAW_DIR.mkdir(parents=True, exist_ok=True)
            HEARTBEAT_PATH.write_text("# Heartbeat\n" + SURVIVAL_HEARTBEAT_BLOCK, encoding="utf-8")
            print(f"[OK] Created {HEARTBEAT_PATH} with agent-survivor tasks.")
            return True
        else:
            print("[SKIP] HEARTBEAT.md not modified.")
            return False

    content = HEARTBEAT_PATH.read_text(encoding="utf-8")
    if "BEGIN agent-survivor heartbeat" in content:
        print("[OK] agent-survivor heartbeat tasks already present in HEARTBEAT.md")
        return True

    # Append safely
    with open(HEARTBEAT_PATH, "a", encoding="utf-8") as f:
        f.write(SURVIVAL_HEARTBEAT_BLOCK)

    print(f"[OK] Appended agent-survivor tasks to {HEARTBEAT_PATH}")
    return True


def main():
    print("=" * 50)
    print("Survival Agent Skill Init")
    print("=" * 50)

    skill_ok = ensure_skill_installed()
    heartbeat_ok = inject_heartbeat()

    print("-" * 50)
    if skill_ok and heartbeat_ok:
        print("Initialization complete!")
        print("Next steps:")
        print("1. Restart your OpenClaw Gateway or send /restart.")
        print("2. The agent will begin checking survival state every 30 minutes.")
    else:
        print("Initialization incomplete. Please fix the warnings above and re-run.")
        sys.exit(1)


if __name__ == "__main__":
    main()
