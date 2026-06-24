#!/usr/bin/env bash
# test_proof.sh — Run a single file through the pipeline and dump all outputs to proofroom/
set -euo pipefail

# Find repo root
find_repo_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/passroom" ]] && [[ -f "$dir/run1time.py" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "$PWD"
}

REPO="$(find_repo_root)"
cd "$REPO"
ENGAIN_ROOT="$(dirname "$REPO")"

PROOF_DIR="$REPO/toolroom/proofroom"
mkdir -p "$PROOF_DIR"

# Input file
INPUT_FILE="${1:-}"
if [[ -z "$INPUT_FILE" ]]; then
    # Find a default test file if none provided
    INPUT_FILE=$(find "$REPO" -maxdepth 3 -name "*contact*.txt" -o -name "03_*.txt" 2>/dev/null | head -1)
    if [[ -z "$INPUT_FILE" ]]; then
        echo "Error: No input file specified and no default found."
        echo "Usage: $0 <path_to_text_file>"
        exit 1
    fi
    echo "No input file specified. Using default: $INPUT_FILE"
fi

INPUT_FILE="$(realpath "$INPUT_FILE")"
if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Error: Input file not found: $INPUT_FILE"
    exit 1
fi

BASENAME="$(basename "$INPUT_FILE" .txt)"
WORLD_RULES="$REPO/manifests/world_rules.json"

echo "═══════════════════════════════════════════════════════"
echo " Pipeline Proof Run"
echo " Input : $INPUT_FILE"
echo " Output: $PROOF_DIR"
echo "═══════════════════════════════════════════════════════"

# Pass 1
echo "[Pass 1] Explicit Extraction..."
cd "$ENGAIN_ROOT" && python3 -m tier3.mettaext.passroom.pass1_explicit "$INPUT_FILE"
P1_FOUND="$(find "$REPO" -name "out_pass1_${BASENAME}.txt" | head -1)"
P1_OUT="$PROOF_DIR/out_pass1_${BASENAME}.txt"

if [[ -z "$P1_FOUND" ]]; then
    echo "[ERROR] Pass 1 output not found: out_pass1_${BASENAME}.txt"
    exit 1
fi

if [[ "$(realpath "$P1_FOUND")" != "$(realpath "$P1_OUT" 2>/dev/null || echo "$P1_OUT")" ]]; then
    cp "$P1_FOUND" "$P1_OUT"
fi

echo "  -> $P1_OUT" 2>/dev/null
echo "  -> $(ls "$PROOF_DIR/out_pass1_${BASENAME}.txt" 2>/dev/null)"

# Pass 2
echo "[Pass 2] Enhanced MeTTa..."
cd "$ENGAIN_ROOT" && python3 -m tier3.mettaext.passroom.pass2_enhanced "$PROOF_DIR/out_pass1_${BASENAME}.txt"
cp "$(find "$REPO" -name "out_pass2_${BASENAME}.metta" | head -1)" "$PROOF_DIR/" 2>/dev/null
echo "  -> $(ls "$PROOF_DIR/out_pass2_${BASENAME}.metta" 2>/dev/null)"

# Pass 3
echo "[Pass 3] ZON-J Merge..."
cd "$ENGAIN_ROOT" && python3 -m tier3.mettaext.passroom.pass3_merge "$PROOF_DIR/out_pass1_${BASENAME}.txt" "$PROOF_DIR/out_pass2_${BASENAME}.metta"
cp "$(find "$REPO" -name "zonj_${BASENAME}.json" | head -1)" "$PROOF_DIR/" 2>/dev/null
echo "  -> $(ls "$PROOF_DIR/zonj_${BASENAME}.json" 2>/dev/null)"

# Pass 4
echo "[Pass 4] ZON Bridge..."
cd "$ENGAIN_ROOT" && python3 -m tier3.mettaext.passroom.pass4_zon_bridge "$PROOF_DIR/zonj_${BASENAME}.json" \
    --era "FirstAge" --location "Beach" \
    --output-dir "$PROOF_DIR" \
    --world-rules "$WORLD_RULES"
echo "  -> $(ls "$PROOF_DIR/${BASENAME}.zon" "$PROOF_DIR/${BASENAME}.zonj.json" 2>/dev/null)"

# Pass 5
echo "[Pass 5] Game Bridge..."
cd "$ENGAIN_ROOT" && python3 -m tier3.mettaext.passroom.pass5_game_bridge "$PROOF_DIR/${BASENAME}.zonj.json" \
    --output "$PROOF_DIR" \
    --world-rules "$WORLD_RULES"
echo "  -> $(ls "$PROOF_DIR/scene.${BASENAME}.json" 2>/dev/null)"

echo
echo "═══════════════════════════════════════════════════════"
echo " Proof Complete. Files in $PROOF_DIR:"
ls -lh "$PROOF_DIR"
echo "═══════════════════════════════════════════════════════"