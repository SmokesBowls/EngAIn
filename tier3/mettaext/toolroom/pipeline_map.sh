#!/usr/bin/env bash
# pipeline_map.sh — Maps the exact input/output contract for every pipeline pass.

set -euo pipefail

# Find repo root
find_repo_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/compiled/pipeline_work" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "$PWD"
}

REPO="$(find_repo_root)"
WORK_DIR="$REPO/compiled/pipeline_work"

echo "═══════════════════════════════════════════════════════"
echo " EngAIn Pipeline Blueprint"
echo " Repo: $REPO"
echo "═══════════════════════════════════════════════════════"
echo

show_pass() {
    local num="$1"
    local script="$2"
    local input_desc="$3"
    local output_pattern="$4"
    local output_dir="$5"
    local description="$6"

    echo "─ PASS $num: $description"
    echo "│  Script : $script"
    echo "│  Input  : $input_desc"
    echo "│  Output : $output_pattern"
    echo "│  Dir    : $output_dir"
    
    # Count actual files on disk
    local count=0
    if [[ -d "$output_dir" ]]; then
        count=$(find "$output_dir" -maxdepth 1 -name "$output_pattern" 2>/dev/null | wc -l)
    fi
    
    if [[ "$count" -gt 0 ]]; then
        echo "│  Status : ✅ $count files generated"
    else
        echo "│  Status : ⚠️  No files found (Pass hasn't run or failed)"
    fi
    echo "└───────────────────────────────────────────────────"
    echo
}

# Pass 1
show_pass "1" \
    "passroom/pass1_explicit.py" \
    "Raw text file (e.g., 03_Fist_contact.txt)" \
    "out_pass1_*.txt" \
    "$WORK_DIR" \
    "Explicit Extraction (LLM pulls raw facts)"

# Pass 2
show_pass "2" \
    "passroom/pass2_enhanced.py" \
    "Pass 1 output (out_pass1_*.txt)" \
    "out_pass2_*.metta" \
    "$WORK_DIR" \
    "Enhanced MeTTa Logic (Structuring & Rules)"

# Pass 3
show_pass "3" \
    "passroom/pass3_merge.py" \
    "Pass 1 + Pass 2 outputs" \
    "zonj_*.json" \
    "$WORK_DIR" \
    "ZON-J Merge (Intermediate JSON format)"

# Pass 4
show_pass "4" \
    "passroom/pass4_zon_bridge.py" \
    "Pass 3 output (zonj_*.json)" \
    "*.zon & *.zonj.json" \
    "$WORK_DIR" \
    "ZON Bridge (Engine-ready zone format)"

# Pass 5
show_pass "5" \
    "passroom/pass5_game_bridge.py" \
    "Pass 4 output (*.zonj.json)" \
    "scene.*.json" \
    "$WORK_DIR/game_scenes" \
    "Game Bridge (Final Godot/Engine scene JSON)"

echo "═══════════════════════════════════════════════════════"
echo " Data Flow Summary"
echo "═══════════════════════════════════════════════════════"
echo "  [Raw .txt] ──(Pass 1)──> [out_pass1_*.txt]"
echo "       │"
echo "       └──(Pass 2)──> [out_pass2_*.metta]"
echo "              │"
echo "              └──(Pass 3)──> [zonj_*.json]"
echo "                     │"
echo "                     └──(Pass 4)──> [*.zon] + [*.zonj.json]"
echo "                            │"
echo "                            └──(Pass 5)──> [scene.*.json]"
echo "═══════════════════════════════════════════════════════"