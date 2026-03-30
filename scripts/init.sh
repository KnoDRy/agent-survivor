#!/usr/bin/env bash
# Survival Agent Skill Init Script (Unix/macOS)
# This script initializes the survival-agent skill by:
# 1. Ensuring the skill directory is installed in the OpenClaw workspace.
# 2. Injecting required heartbeat tasks into ~/.openclaw/HEARTBEAT.md (if not already present).

set -e

OPENCLAW_DIR="$HOME/.openclaw"
HEARTBEAT_PATH="$OPENCLAW_DIR/HEARTBEAT.md"
SKILL_TARGET="$OPENCLAW_DIR/workspace/skills/survival-agent"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SURVIVAL_HEARTBEAT_BLOCK=$'\n<!-- BEGIN survival-agent heartbeat -->\n## Survival Agent Check (every 30 minutes)\n- Read `~/.openclaw/workspace/skills/survival-agent/state.json`.\n- Apply decay rules based on elapsed time since `last_updated`.\n- Run the survival decision tree once (cook / forage / play / doctor / explore / relax).\n- Write updated state back.\n\n## Survival Agent Morning Plan (08:00 daily)\n- Read state and plan files.\n- Write today\'s goals to `~/.openclaw/workspace/skills/survival-agent/plan.md`.\n- Clear `today_events` in state.\n\n## Survival Agent Evening Review (22:00 daily)\n- Assess plan completion and append review to plan.md.\n- Write diary entry to `~/.openclaw/workspace/skills/survival-agent/diary/YYYY-MM-DD.md`.\n<!-- END survival-agent heartbeat -->\n'

echo "=================================================="
echo "Survival Agent Skill Init"
echo "=================================================="

# Ensure skill installed
if [ -d "$SKILL_TARGET" ]; then
    echo "[OK] Skill already installed at: $SKILL_TARGET"
else
    echo "[WARN] Skill not found at expected location: $SKILL_TARGET"
    echo "[INFO] Current directory: $CURRENT_DIR"

    if [ "$(basename "$CURRENT_DIR")" = "survival-agent" ]; then
        read -rp "Would you like to copy the current directory to the OpenClaw skills folder? [Y/n] " answer
        answer=${answer:-y}
        if [[ "$answer" =~ ^[Yy]$ ]]; then
            mkdir -p "$(dirname "$SKILL_TARGET")"
            cp -R "$CURRENT_DIR" "$SKILL_TARGET"
            echo "[OK] Copied skill to: $SKILL_TARGET"
        else
            echo "[SKIP] Skill not copied. Please copy it manually."
            exit 1
        fi
    else
        echo "[SKIP] Please copy the survival-agent directory to:"
        echo "       $SKILL_TARGET"
        exit 1
    fi
fi

# Inject heartbeat
if [ -f "$HEARTBEAT_PATH" ]; then
    if grep -q "BEGIN survival-agent heartbeat" "$HEARTBEAT_PATH"; then
        echo "[OK] survival-agent heartbeat tasks already present in HEARTBEAT.md"
    else
        printf '%s' "$SURVIVAL_HEARTBEAT_BLOCK" >> "$HEARTBEAT_PATH"
        echo "[OK] Appended survival-agent tasks to $HEARTBEAT_PATH"
    fi
else
    echo "[WARN] HEARTBEAT.md not found at: $HEARTBEAT_PATH"
    read -rp "Create a new HEARTBEAT.md with survival-agent tasks? [Y/n] " answer
    answer=${answer:-y}
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        mkdir -p "$OPENCLAW_DIR"
        printf '# Heartbeat\n%s' "$SURVIVAL_HEARTBEAT_BLOCK" > "$HEARTBEAT_PATH"
        echo "[OK] Created $HEARTBEAT_PATH with survival-agent tasks."
    else
        echo "[SKIP] HEARTBEAT.md not modified."
        exit 1
    fi
fi

echo "--------------------------------------------------"
echo "Initialization complete!"
echo "Next steps:"
echo "1. Restart your OpenClaw Gateway or send /restart."
echo "2. The agent will begin checking survival state every 30 minutes."
