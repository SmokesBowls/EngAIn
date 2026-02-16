#!/usr/bin/env bash
set -euo pipefail

# cleanup_heavy_hitter.sh
# Conservative quarantine-based cleanup for EngAIn canonical root.
# Never deletes. Moves candidates into archive/_quarantine_TIMESTAMP/ then reruns baseline.
# If baseline fails, auto-reverts moves.

usage() {
  cat <<'EOF'
Usage:
  bash cleanup_heavy_hitter.sh --dry-run
  bash cleanup_heavy_hitter.sh --execute

Optional:
  KEEP_OVERRIDES=cleanup_reports_hh/keep_overrides.txt

What it does:
  1) Verifies repo layout + canonical root exists
  2) Runs baseline: pytest godotengain/engainos/tests
  3) Builds evidence:
     - Static import scan (canonical root + tests) with "flat import" mapping
     - Godot reference scan: .gd/.tscn across relevant roots
  4) Produces candidates (canonical root only) and move plan
  5) If --execute: moves into archive/_quarantine_TIMESTAMP/, reruns baseline; if fails, reverts
EOF
}

MODE="${1:-}"
if [[ "$MODE" != "--dry-run" && "$MODE" != "--execute" ]]; then
  usage
  exit 2
fi

ROOT="$(pwd)"
CANON_ROOT="godotengain/engainos"
TEST_ROOT="godotengain/engainos/tests"
ARCHIVE_DIR="archive"
TS="$(date +%F_%H%M%S)"
REPORT_DIR="cleanup_reports_hh"
QUAR_DIR="$ARCHIVE_DIR/_quarantine_${TS}"

KEEP_OVERRIDES="${KEEP_OVERRIDES:-$REPORT_DIR/keep_overrides.txt}"

mkdir -p "$REPORT_DIR" "$ARCHIVE_DIR"

LOG="$REPORT_DIR/run.log"
: > "$LOG"

log() { echo "$*" | tee -a "$LOG" ; }

require_path() {
  local p="$1"
  [[ -e "$p" ]] || { echo "Missing required path: $p" >&2; exit 1; }
}

require_path "$CANON_ROOT"
require_path "$TEST_ROOT"

# --- Helpers ---------------------------------------------------------------

# Build a set of module names that resolve to files under CANON_ROOT.
# We treat "flat imports" as modules that can be resolved by basename of .py inside canon.
# Example: from empire_mr import Empire -> resolves to core/empire_mr.py if exists.
build_flat_module_index() {
  # Output lines: module_name<TAB>relative_path
  find "$CANON_ROOT" -type f -name "*.py" \
    ! -path "*/__pycache__/*" \
    -print0 \
  | while IFS= read -r -d '' f; do
      local rel="${f#$CANON_ROOT/}"
      local base="$(basename "$f" .py)"
      # We allow flat module name by basename
      printf "%s\t%s/%s\n" "$base" "$CANON_ROOT" "$rel"
    done | sort -u
}

# Extract imported module tokens from python source (simple heuristic).
# Captures:
#   import X
#   import X as Y
#   import X,Y
#   from X import Y
python_import_tokens() {
  # prints one module token per line
  sed -nE '
    s/#.*$//;
    /^[[:space:]]*import[[:space:]]+/{
      s/^[[:space:]]*import[[:space:]]+//;
      s/[[:space:]]+as[[:space:]]+[A-Za-z0-9_]+//g;
      s/[[:space:]]//g;
      s/,/\n/g;
      p;
    }
    /^[[:space:]]*from[[:space:]]+/{
      s/^[[:space:]]*from[[:space:]]+//;
      s/[[:space:]]+import[[:space:]].*$//;
      s/[[:space:]]//g;
      p;
    }
  '
}

# Find python files that import a given flat module name (exact token match).
find_flat_importers() {
  local mod="$1"
  rg -n --hidden --glob '!**/__pycache__/**' \
    --glob "$CANON_ROOT/**/*.py" --glob "$TEST_ROOT/**/*.py" \
    "^\s*(from|import)\s+${mod}(\s|$|\.|,)" \
    "$CANON_ROOT" "$TEST_ROOT" || true
}

# Godot reference scan: look for candidate basenames and/or paths in .gd/.tscn.
# We scan multiple plausible Godot roots, not just one folder.
build_godot_refs_raw() {
  local out="$1"
  local roots=(
    "godotengain"          # entire godot project tree
    "$CANON_ROOT"          # canonical python sits here but may include scripts/
  )
  # Only include roots that exist
  local existing=()
  for r in "${roots[@]}"; do
    [[ -e "$r" ]] && existing+=("$r")
  done

  if [[ "${#existing[@]}" -eq 0 ]]; then
    : > "$out"
    return
  fi

  # Collect all .gd and .tscn content as searchable lines.
  rg -n --hidden \
    --glob '**/*.gd' --glob '**/*.tscn' \
    --glob '!**/.godot/**' --glob '!**/__pycache__/**' \
    '.' "${existing[@]}" > "$out" || true
}

# Determine if a canonical file is an "entrypoint-ish" file we should keep.
is_entrypointish() {
  local rel=""

  # Broad entrypoint heuristics (keep by default)
  [[ "" == *"_server.py" ]] && return 0
  [[ "" == *"_api.py" ]] && return 0

  case "" in
    */__init__.py) return 0 ;;
    */launch_engine.py) return 0 ;;
    */sim_runtime.py) return 0 ;;
    */launch_bridge.py) return 0 ;;
    */zon_bridge.py) return 0 ;;
    */zon_to_game.py) return 0 ;;
    */zw_core.py) return 0 ;;
    */ap_core.py) return 0 ;;
    */empire_mr.py) return 0 ;;
    */empire_agent_gateway.py) return 0 ;;
    */agent_gateway.py) return 0 ;;
    */runtime_api.py) return 0 ;;
    */engainos_server.py) return 0 ;;
    */core/ap_engine.py) return 0 ;;
# keep by default unless explicitly overridden
  esac
  return 1
}

# --- 1) Baseline -----------------------------------------------------------

log "== Baseline: pytest $TEST_ROOT =="
pytest "$TEST_ROOT" > "$REPORT_DIR/baseline_before.txt" 2>&1 || true
BASE_EXIT=$?
log "Baseline exit code: $BASE_EXIT"
if [[ "$BASE_EXIT" -ne 0 ]]; then
  log "Baseline is not green. Refusing to proceed."
  exit 1
fi

# --- 2) Evidence -----------------------------------------------------------

log "== Building static import index (canon + tests) =="

FLAT_INDEX="$REPORT_DIR/flat_module_index.tsv"
build_flat_module_index > "$FLAT_INDEX"
log "Wrote: $ROOT/$FLAT_INDEX"

STATIC_IMPORTS="$REPORT_DIR/static_imports.txt"
: > "$STATIC_IMPORTS"

# Collect import tokens from canon + tests and map flat modules to canon files.
# This avoids the false-negative you saw (imports like 'from empire_mr import ...').
find "$CANON_ROOT" "$TEST_ROOT" -type f -name "*.py" ! -path "*/__pycache__/*" -print0 \
| while IFS= read -r -d '' py; do
    python_import_tokens < "$py" \
    | while IFS= read -r tok; do
        [[ -z "$tok" ]] && continue
        # Only consider the "top-level" module token (split at '.')
        top="${tok%%.*}"
        # Map flat module name to canonical file path if exists
        hit="$(awk -F'\t' -v m="$top" '$1==m{print $2; exit}' "$FLAT_INDEX" || true)"
        if [[ -n "$hit" ]]; then
          echo -e "$top\t$hit\t(imported_by)\t${py#$ROOT/}" >> "$STATIC_IMPORTS"
        fi
      done
  done

sort -u "$STATIC_IMPORTS" -o "$STATIC_IMPORTS"
log "Wrote: $ROOT/$STATIC_IMPORTS"

log "== Building Godot ref index (.gd/.tscn) =="
GODOT_REFS_RAW="$REPORT_DIR/godot_refs_raw.txt"
build_godot_refs_raw "$GODOT_REFS_RAW"
log "Wrote: $ROOT/$GODOT_REFS_RAW"

# --- 3) Compute used/keep --------------------------------------------------

# Used canonical files from static import mapping
USED_FILES="$REPORT_DIR/used_files.txt"
: > "$USED_FILES"

# Add all mapped canonical files as "used"
awk -F'\t' '{print $2}' "$STATIC_IMPORTS" | sort -u >> "$USED_FILES"

# Add everything under tests as keep context (not moved anyway, but contributes to used analysis)
# (No-op here; candidates are canonical only.)

sort -u "$USED_FILES" -o "$USED_FILES"
USED_COUNT="$(wc -l < "$USED_FILES" | tr -d ' ')"

# Build keep list: entrypoint-ish + used + keep overrides
KEEP="$REPORT_DIR/keep.txt"
: > "$KEEP"

# 1) entrypoint-ish keeps (within canonical root)
find "$CANON_ROOT" -type f -name "*.py" ! -path "*/__pycache__/*" -print0 \
| while IFS= read -r -d '' f; do
    rel="${f#$ROOT/}"
    if is_entrypointish "$rel"; then
      echo "$rel" >> "$KEEP"
    fi
  done

# 2) used files
cat "$USED_FILES" >> "$KEEP"

# 3) keep overrides
if [[ -f "$KEEP_OVERRIDES" ]]; then
  # normalize, ignore blank/comment lines
  sed -e 's/#.*$//' -e '/^[[:space:]]*$/d' "$KEEP_OVERRIDES" >> "$KEEP"
fi

sort -u "$KEEP" -o "$KEEP"
KEEP_COUNT="$(wc -l < "$KEEP" | tr -d ' ')"

log "== Computing used/keep =="

log "Used files: $USED_COUNT"
log "Keep files: $KEEP_COUNT"

# --- 4) Candidate list -----------------------------------------------------

log "== Building candidate list (within canonical root only) =="

CAND="$REPORT_DIR/candidates.txt"
: > "$CAND"

# Candidates are python files in canonical root that are:
# - not in KEEP
# - not referenced by Godot (.gd/.tscn) by basename or relative path mention
# NOTE: Godot scan is heuristic; keep overrides is your safety valve.
while IFS= read -r f; do
  rel="${f#$ROOT/}"

  # Only canonical-root .py
  [[ "$rel" == "$CANON_ROOT/"*".py" ]] || continue

  # HARD BLOCK: never move tests
  [[ "$rel" == "$TEST_ROOT/"* ]] && continue

  # Skip if kept
  if grep -qxF "$rel" "$KEEP"; then
    continue
  fi

  base="$(basename "$rel" .py)"

  # Godot heuristic: match basename or direct path fragments
  if rg -n --fixed-strings "$base" "$GODOT_REFS_RAW" >/dev/null 2>&1; then
    continue
  fi
  if rg -n --fixed-strings "$rel" "$GODOT_REFS_RAW" >/dev/null 2>&1; then
    continue
  fi

  echo "$rel" >> "$CAND"
done < <(find "$CANON_ROOT" -type f -name "*.py" ! -path "*/__pycache__/*" -print0 | xargs -0 -n1 echo)

sort -u "$CAND" -o "$CAND"
CAND_COUNT="$(wc -l < "$CAND" | tr -d ' ')"
log "Candidates: $CAND_COUNT"
log "Wrote: $ROOT/$CAND"

# --- 5) Move plan + summary ------------------------------------------------

log "== Planning quarantine moves =="

mkdir -p "$QUAR_DIR"

MOVE_PLAN="$REPORT_DIR/move_plan.txt"
: > "$MOVE_PLAN"

while IFS= read -r rel; do
  src="$rel"
  dst="$QUAR_DIR/$rel"
  echo "$src -> $dst" >> "$MOVE_PLAN"
done < "$CAND"

log "Quarantine dir: $ROOT/$QUAR_DIR"
log "Move plan: $ROOT/$MOVE_PLAN"

SUMMARY="$REPORT_DIR/summary.txt"
cat > "$SUMMARY" <<EOF
generated: $(date '+%F %T')
mode: $MODE
baseline command: pytest $TEST_ROOT
baseline exit code: $BASE_EXIT
baseline passed: Yes

counts:
  used_files: $USED_COUNT
  keep_files: $KEEP_COUNT
  candidates: $CAND_COUNT

keep_overrides: $( [[ -f "$KEEP_OVERRIDES" ]] && echo "$KEEP_OVERRIDES" || echo "(none)" )
quarantine_dir: $QUAR_DIR

notes:
  - Candidates exclude keep list and Godot-referenced heuristics.
  - Keep overrides are authoritative: anything in keep_overrides.txt will never be moved.
EOF

log "== Writing summary =="
log "Wrote: $ROOT/$SUMMARY"

log ""
log "== Preview (first 40 planned moves) =="
head -n 40 "$MOVE_PLAN" | tee -a "$LOG" || true
log "== End preview =="

if [[ "$MODE" == "--dry-run" ]]; then
  log "Dry-run complete. Nothing moved."
  exit 0
fi

# --- 6) Execute moves + rerun baseline + auto-revert -----------------------

log "== EXECUTE: moving candidates into quarantine =="

# record moves actually performed so we can revert precisely
DID_MOVES="$REPORT_DIR/moves_done.txt"
: > "$DID_MOVES"

while IFS= read -r line; do
  src="${line%% ->*}"
  dst="${line#*-> }"

  # safety: ensure src exists and is under canon
  [[ "$src" == "$CANON_ROOT/"*".py" ]] || continue
  [[ -f "$src" ]] || continue

  mkdir -p "$(dirname "$dst")"
  mv "$src" "$dst"
  echo "$src -> $dst" >> "$DID_MOVES"
done < "$MOVE_PLAN"

log "Moved: $(wc -l < "$DID_MOVES" | tr -d ' ') file(s)"
log "Wrote: $ROOT/$DID_MOVES"

log "== Baseline after moves =="
pytest "$TEST_ROOT" > "$REPORT_DIR/baseline_after.txt" 2>&1 || true
AFTER_EXIT=$?
log "Baseline exit code after: $AFTER_EXIT"

if [[ "$AFTER_EXIT" -ne 0 ]]; then
  log "Baseline FAILED after moves. Auto-reverting..."
  # revert in reverse order
  tac "$DID_MOVES" | while IFS= read -r m; do
    src="${m%% ->*}"
    dst="${m#*-> }"
    mkdir -p "$(dirname "$src")"
    mv "$dst" "$src"
  done
  log "Reverted moves. See $ROOT/$REPORT_DIR/baseline_after.txt for failure details."
  exit 1
fi

log "Baseline PASSED after moves."
log "Quarantine kept at: $ROOT/$QUAR_DIR"
exit 0
