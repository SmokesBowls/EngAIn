#!/usr/bin/env bash
# passview.sh — Quick inspector for mettaext pipeline pass outputs
# Usage: ./passview.sh [1|2|3|4|5|all] [num_lines]

set -euo pipefail

# Auto-detect repo root (look for compiled/pipeline_work)
find_repo_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/compiled/pipeline_work" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "Error: Could not find repo root (no compiled/pipeline_work found)" >&2
    return 1
}

REPO_ROOT="$(find_repo_root)"
BASE="$REPO_ROOT/compiled/pipeline_work"
LINES="${2:-20}"

declare -A PATTERNS LOCATIONS DESC
PATTERNS[1]="out_pass1_*.txt"
PATTERNS[2]="out_pass2_*.metta"
PATTERNS[3]="zonj_*.json"
PATTERNS[4]="*.zon"
PATTERNS[5]="game_scenes/scene.*.json"

LOCATIONS[1]="."
LOCATIONS[2]="."
LOCATIONS[3]="."
LOCATIONS[4]="."
LOCATIONS[5]="game_scenes"

DESC[1]="Pass 1 — Explicit extraction (txt)"
DESC[2]="Pass 2 — Enhanced MeTTa logic (metta)"
DESC[3]="Pass 3 — ZON-J intermediate JSON (zonj)"
DESC[4]="Pass 4 — ZON bridge output (zon)"
DESC[5]="Pass 5 — Final game scenes (json)"

show_pass() {
    local p="$1"
    local dir="$BASE/${LOCATIONS[$p]}"
    local pat="${PATTERNS[$p]}"
    
    echo "═══════════════════════════════════════════════════════"
    echo " ${DESC[$p]}"
    echo "═══════════════════════════════════════════════════════"
    echo " Repo     : $REPO_ROOT"
    echo " Location : $dir/"
    echo " Pattern  : $pat"
    
    if [[ ! -d "$dir" ]]; then
        echo " ⚠  Directory not found."
        echo
        return
    fi
    
    local count
    count=$(find "$dir" -maxdepth 1 -name "$pat" 2>/dev/null | wc -l)
    echo " Files    : $count"
    
    if [[ "$count" -eq 0 ]]; then
        echo " ⚠  No matching files."
        echo
        return
    fi
    
    local total_size
    total_size=$(find "$dir" -maxdepth 1 -name "$pat" -exec du -cb {} + 2>/dev/null | tail -1 | cut -f1)
    local human_size
    human_size=$(numfmt --to=iec-i --suffix=B "$total_size" 2>/dev/null || echo "${total_size}B")
    echo " Total    : $human_size"
    
    echo " Samples  :"
    find "$dir" -maxdepth 1 -name "$pat" | head -5 | while read -r f; do
        local sz
        sz=$(du -h "$f" | cut -f1)
        printf "   • %-50s [%s]\n" "$(basename "$f")" "$sz"
    done
    if [[ "$count" -gt 5 ]]; then
        echo "   ... and $((count - 5)) more"
    fi
    
    local first
    first=$(find "$dir" -maxdepth 1 -name "$pat" | sort | head -1)
    echo
    echo " Preview  : $(basename "$first") (first $LINES lines)"
    echo "───────────────────────────────────────────────────────"
    head -n "$LINES" "$first"
    echo "───────────────────────────────────────────────────────"
    echo
}

if [[ $# -eq 0 ]]; then
    echo "Usage: $0 [1|2|3|4|5|all] [preview_lines]"
    echo
    echo "Examples:"
    echo "  $0 2        # Inspect pass 2 output"
    echo "  $0 all      # Inspect all passes"
    echo "  $0 4 50     # Inspect pass 4, show 50 lines"
    exit 1
fi

TARGET="${1:-all}"

if [[ "$TARGET" == "all" ]]; then
    for i in 1 2 3 4 5; do
        show_pass "$i"
    done
elif [[ "$TARGET" =~ ^[1-5]$ ]]; then
    show_pass "$TARGET"
else
    echo "Error: Pass must be 1, 2, 3, 4, 5, or 'all'"
    exit 1
fi