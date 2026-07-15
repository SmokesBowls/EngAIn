#!/usr/bin/env bash
set -euo pipefail

SESSION="engain_stack"

GODOT_PATH="/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender"
UPBGE_DIR="/home/burdens/Applications/upbge-0.50-linux-x64"
UPBGE_BLEND="/home/burdens/burdens_of_a_forgotten_past/EngAIn/upbge/one_path.blend"
SIM_DIR="/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim"
AP_DIR="/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos"
VAULT_DIR="/home/burdens/obsidian/obsidianburdenNov25"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1" >&2; exit 1; }; }
port_in_use() { ss -ltn 2>/dev/null | awk '{print $4}' | grep -qE "127\.0\.0\.1:$1$"; }

need tmux
need ss
need python3
need godot

if tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux attach -t "$SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n "sim8080"

tmux send-keys -t "$SESSION:sim8080" "cd \"$SIM_DIR\"" C-m
tmux send-keys -t "$SESSION:sim8080" "if port_in_use 8080; then echo '[sim8080] port 8080 already in use'; else python3 sim_runtime.py; fi" C-m

tmux new-window -t "$SESSION" -n "ap8765"
tmux send-keys -t "$SESSION:ap8765" "cd \"$AP_DIR\"" C-m
tmux send-keys -t "$SESSION:ap8765" "if port_in_use 8765; then echo '[ap8765] port 8765 already in use'; else python3 launch_engine.py; fi" C-m

tmux new-window -t "$SESSION" -n "http8090"
tmux send-keys -t "$SESSION:http8090" "cd \"$AP_DIR\"" C-m
tmux send-keys -t "$SESSION:http8090" "if port_in_use 8090; then echo '[http8090] port 8090 already in use'; else python3 -m uvicorn engainos_server:app --host 127.0.0.1 --port 8090; fi" C-m

tmux new-window -t "$SESSION" -n "godot"
tmux send-keys -t "$SESSION:godot" "cd \"$GODOT_PATH\"" C-m
tmux send-keys -t "$SESSION:godot" "godot --path \"$GODOT_PATH\" --editor" C-m

tmux new-window -t "$SESSION" -n "upbge"
tmux send-keys -t "$SESSION:upbge" "cd \"$UPBGE_DIR\"" C-m
tmux send-keys -t "$SESSION:upbge" "./blender \"$UPBGE_BLEND\"" C-m

tmux new-window -t "$SESSION" -n "vault"
tmux send-keys -t "$SESSION:vault" "cd \"$VAULT_DIR\" && pwd && ls -la | head" C-m

tmux select-window -t "$SESSION:sim8080"
tmux attach -t "$SESSION"
