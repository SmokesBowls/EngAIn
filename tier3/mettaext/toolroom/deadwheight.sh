#!/usr/bin/env bash
# deadweight.sh — Find dead, orphaned, and ghost Python scripts
# Usage: ./deadweight.sh

set -euo pipefail

# Find repo root
find_repo_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/master_pipeline.py" ]] || [[ -d "$dir/passroom" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "$PWD"
}

REPO="$(find_repo_root)"
cd "$REPO"

echo "═══════════════════════════════════════════════════════"
echo " Dead Weight Detector — $REPO"
echo "═══════════════════════════════════════════════════════"
echo

# Collect all .py files (exclude __pycache__, venv, .git)
mapfile -t PY_FILES < <(find . -type f -name "*.py" \
    -not -path "*/__pycache__/*" \
    -not -path "*/.venv/*" \
    -not -path "*/venv/*" \
    -not -path "*/.git/*" | sort)

# Recently used (in __pycache__)
mapfile -t CACHED < <(find . -path "*/__pycache__/*.pyc" -exec basename {} \; 2>/dev/null \
    | sed -E 's/\.cpython-[0-9]+\.pyc$//' | sort -u)

# Active imports/calls across all files
ACTIVE_REFS=$(grep -rEoh "[A-Za-z_][A-Za-z0-9_]*\.py" --include="*.py" --include="*.sh" . 2>/dev/null \
    | sort -u)
ACTIVE_IMPORTS=$(grep -rEoh "^(import|from)\s+[A-Za-z_][A-Za-z0-9_.]*" --include="*.py" . 2>/dev/null \
    | awk '{print $2}' | awk -F. '{print $NF}' | sort -u)

echo "📋 Analyzing ${#PY_FILES[@]} Python files..."
echo

ORPHANS=()
GHOSTS=()
DUPLICATES=()
ACTIVE=()

for pyf in "${PY_FILES[@]}"; do
    base=$(basename "$pyf")
    stem="${base%.py}"
    rel="${pyf#./}"
    
    # Skip __init__.py (they're structural)
    [[ "$base" == "__init__.py" ]] && continue
    
    # Check: is it referenced by name anywhere?
    referenced=false
    # Direct filename reference (subprocess, open, etc.)
    if echo "$ACTIVE_REFS" | grep -qx "$base"; then
        referenced=true
    fi
    # Module import
    if echo "$ACTIVE_IMPORTS" | grep -qx "$stem"; then
        referenced=true
    fi
    # Referenced in shell scripts
    if grep -rq "$base\|$stem" --include="*.sh" . 2>/dev/null; then
        referenced=true
    fi
    # Referenced in other .py (loose match on stem)
    if grep -rEq "(^|[\"'/ ])${stem}(\.py|['\"]|\\s|$)" --include="*.py" . 2>/dev/null \
       && ! grep -lEq "(^|[\"'/ ])${stem}(\.py|['\"]|\\s|$)" --include="*.py" . 2>/dev/null | grep -qx "$pyf"; then
        referenced=true
    fi
    
    # Check: recently executed?
    recent=false
    if printf '%s\n' "${CACHED[@]}" | grep -qx "$stem"; then
        recent=true
    fi
    
    # Check: executable?
    executable=false
    if head -1 "$pyf" | grep -q "^#!"; then
        executable=true
    fi
    if grep -q "if __name__ == .__main__" "$pyf"; then
        executable=true
    fi
    
    # Check: referenced but file doesn't exist (GHOST) — we're iterating existing files,
    # so ghosts are detected separately below
    
    # Classify
    if $referenced || $recent; then
        ACTIVE+=("$rel|$recent|$referenced")
    else
        ORPHANS+=("$rel|$executable")
    fi
done

# ─────────────────────────────────────────────────────────
# GHOST detection: files referenced in code but don't exist
# ─────────────────────────────────────────────────────────
mapfile -t GHOST_REFS < <(grep -rEoh "[A-Za-z_][A-Za-z0-9_]+\.py" --include="*.py" --include="*.sh" . 2>/dev/null \
    | sort -u | while read ref; do
        base="$(basename "$ref")"

        # Treat moved passroom files as valid.
        # This prevents false ghosts after the mettaext pass files moved from root into passroom/.
        exists=false
        if [[ -f "$ref" ]]; then
            exists=true
        elif [[ -f "$base" ]]; then
            exists=true
        elif [[ -f "passroom/$base" ]]; then
            exists=true
        elif [[ "$base" == "sim_runtime.py" && -f "../godotsim/sim_runtime.py" ]]; then
            exists=true
        elif [[ "$base" == "start_button.py" ]]; then
            # start_button is a system-launch concept/reference, not a mettaext-owned file.
            exists=true
        elif [[ "$base" == "__init__.py" ]]; then
            exists=true
        fi

        if ! $exists; then
            # Find who references it
            callers=$(grep -rlE "(^|[\"'/ ])$base" --include="*.py" --include="*.sh" . 2>/dev/null | head -3 | tr '\n' ',' | sed 's/,$//')
            echo "$ref|$callers"
        fi
    done)

# ─────────────────────────────────────────────────────────
# DUPLICATE detection: files with very similar stems
# ─────────────────────────────────────────────────────────
declare -A STEM_GROUPS
for pyf in "${PY_FILES[@]}"; do
    base=$(basename "$pyf")
    stem="${base%.py}"
    [[ "$base" == "__init__.py" ]] && continue
    # Normalize: strip passN_, out_, zw_, etc.
    key=$(echo "$stem" | sed -E 's/^(pass[0-9]+_|out_|zw_|scene_)/\1/')
    STEM_GROUPS["$key"]+="$pyf "
done

# ─────────────────────────────────────────────────────────
# OUTPUT
# ─────────────────────────────────────────────────────────

echo "✅ ACTIVE (referenced or recently executed): ${#ACTIVE[@]}"
printf '   %-50s %s\n' "FILE" "STATUS"
printf '   %-50s %s\n' "──────────────────────────────────────────────────" "──────────────"
for entry in "${ACTIVE[@]}"; do
    IFS='|' read -r file recent refs <<< "$entry"
    status=""
    $recent && status+="🔥recent "
    $refs   && status+="🔗linked"
    printf '   %-50s %s\n' "$file" "$status"
done

echo
echo "💀 ORPHANS (never referenced, never recently run): ${#ORPHANS[@]}"
printf '   %-50s %s\n' "FILE" "NOTES"
printf '   %-50s %s\n' "──────────────────────────────────────────────────" "──────────────"
for entry in "${ORPHANS[@]}"; do
    IFS='|' read -r file executable <<< "$entry"
    note=""
    $executable && note="has __main__ (CLI tool?)" || note="no entrypoint, no refs"
    printf '   \e[31m%-50s\e[0m %s\n' "$file" "$note"
done

echo
echo "👻 GHOSTS (referenced but file doesn't exist): ${#GHOST_REFS[@]}"
for entry in "${GHOST_REFS[@]}"; do
    [[ -z "$entry" ]] && continue
    IFS='|' read -r ghost callers <<< "$entry"
    printf '   \e[33m%-40s\e[0m ← called by: %s\n' "$ghost" "$callers"
done

echo
echo "🔁 POTENTIAL DUPLICATES (same prefix cluster):"
found_dup=false
for key in "${!STEM_GROUPS[@]}"; do
    files=(${STEM_GROUPS[$key]})
    if [[ ${#files[@]} -gt 1 ]]; then
        # Check if they share more than just a prefix
        stems=()
        for f in "${files[@]}"; do
            stems+=("$(basename "${f%.py}")")
        done
        # Look for pass2_*, zw_*, etc. clusters
        prefix=$(echo "${stems[0]}" | grep -oE "^(pass[0-9]+_|zw_|scene_|out_pass[0-9]+_)" || true)
        if [[ -n "$prefix" ]]; then
            count=0
            matches=()
            for s in "${stems[@]}"; do
                if [[ "$s" == ${prefix}* ]]; then
                    matches+=("$s")
                    ((count++))
                fi
            done
            if [[ $count -gt 1 ]]; then
                printf '   \e[36m%s\e[0m variants: %s\n' "$prefix" "${matches[*]}"
                found_dup=true
            fi
        fi
    fi
done
$found_dup || echo "   (none detected)"

echo
echo "═══════════════════════════════════════════════════════"
echo " Summary"
echo "═══════════════════════════════════════════════════════"
echo "   Total .py files : ${#PY_FILES[@]}"
echo "   Active          : ${#ACTIVE[@]}"
echo "   Orphans (dead)  : ${#ORPHANS[@]}"
echo "   Ghosts (missing): ${#GHOST_REFS[@]}"
echo "═══════════════════════════════════════════════════════"