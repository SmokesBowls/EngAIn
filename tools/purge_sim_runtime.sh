#!/usr/bin/env bash
set -euo pipefail

# purge_sim_runtime.sh
# Safe purge of duplicate sim_runtime.py files.
# Default: DRY RUN. Use --apply to actually delete.

ROOT="${1:-/home/burdens/burdens_of_a_forgotten_past/EngAIn}"

# Path to keep (your renamed runtime or canonical one).
# Set this to the file you want to preserve.
KEEP="${KEEP:-}"

# Options
APPLY=0
BACKUP=1
BACKUP_DIR="${BACKUP_DIR:-${ROOT}/.trash_sim_runtime_$(date +%Y%m%d_%H%M%S)}"

usage() {
  cat <<EOF
Usage:
  KEEP=/abs/path/to/keep.py $0 [ROOT] [--apply] [--no-backup]

Examples:
  # Dry-run list only
  $0 /home/burdens/burdens_of_a_forgotten_past/EngAIn

  # Keep a specific file, dry-run
  KEEP=/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim/sim_runtime_KEEP.py $0

  # Actually delete (with backups)
  KEEP=/path/to/keep.py $0 /home/burdens/burdens_of_a_forgotten_past/EngAIn --apply

  # Actually delete (no backups)
  KEEP=/path/to/keep.py $0 /home/burdens/burdens_of_a_forgotten_past/EngAIn --apply --no-backup
EOF
}

# Parse args
for arg in "${@:2}"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --no-backup) BACKUP=0 ;;
    -h|--help) usage; exit 0 ;;
    *) ;;
  esac
done

ROOT="$(python3 - <<'PY'
import os,sys
print(os.path.abspath(sys.argv[1]))
PY
"$ROOT")"

if [[ -n "${KEEP}" ]]; then
  KEEP="$(python3 - <<'PY'
import os,sys
print(os.path.abspath(sys.argv[1]))
PY
"$KEEP")"
fi

echo "ROOT:  ${ROOT}"
echo "KEEP:  ${KEEP:-<none>}"
echo "MODE:  $([[ $APPLY -eq 1 ]] && echo DELETE || echo DRY-RUN)"
echo "BACKUP:$([[ $BACKUP -eq 1 ]] && echo ON || echo OFF)"
echo

mapfile -t CANDIDATES < <(find "$ROOT" -type f -name 'sim_runtime.py' 2>/dev/null | sort)

if [[ ${#CANDIDATES[@]} -eq 0 ]]; then
  echo "No sim_runtime.py found under ROOT."
  exit 0
fi

echo "Found ${#CANDIDATES[@]} sim_runtime.py files:"
printf '  %s\n' "${CANDIDATES[@]}"
echo

# Build deletion list
DELETE_LIST=()
for f in "${CANDIDATES[@]}"; do
  if [[ -n "${KEEP}" && "$f" == "$KEEP" ]]; then
    echo "KEEPING: $f"
    continue
  fi
  DELETE_LIST+=("$f")
done

echo
echo "Would delete ${#DELETE_LIST[@]} file(s):"
printf '  %s\n' "${DELETE_LIST[@]}"
echo

if [[ $APPLY -ne 1 ]]; then
  echo "DRY RUN only. Re-run with --apply to delete."
  exit 0
fi

# Apply: backup then delete
if [[ $BACKUP -eq 1 ]]; then
  mkdir -p "$BACKUP_DIR"
  echo "Backing up to: $BACKUP_DIR"
fi

for f in "${DELETE_LIST[@]}"; do
  if [[ $BACKUP -eq 1 ]]; then
    rel="${f#"$ROOT"/}"
    dst="${BACKUP_DIR}/${rel}"
    mkdir -p "$(dirname "$dst")"
    cp -av "$f" "$dst" >/dev/null
  fi
  rm -f "$f"
  echo "DELETED: $f"
done

echo
if [[ $BACKUP -eq 1 ]]; then
  echo "DONE. Backups stored in: $BACKUP_DIR"
else
  echo "DONE. No backups were made."
fi
