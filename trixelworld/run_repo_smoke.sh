#!/usr/bin/env bash
set -u -o pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
TASK_TIMEOUT="${TASK_TIMEOUT:-180}"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
OUT_ROOT="${OUT_ROOT:-/tmp/trixel_smoke_${RUN_ID}}"
LOG_DIR="$OUT_ROOT/logs"
STATUS_FILE="$OUT_ROOT/status.tsv"

mkdir -p "$LOG_DIR"
ln -sfn "$OUT_ROOT" /tmp/trixel_smoke_latest

declare -a LABELS=()
declare -a CMDS=()

add_task() {
    LABELS+=("$1")
    CMDS+=("$2")
}

# Known runnable entrypoints / tests.
# Pure library modules are intentionally skipped.
add_task "debugerrors"          "$PYTHON_BIN debugerrors.py"
add_task "debugnames"           "$PYTHON_BIN debugnames.py"
add_task "test_spacing_ratio"   "$PYTHON_BIN test_spacing_ratio.py"
add_task "test_parse"           "$PYTHON_BIN test_parse.py"
add_task "test_gflare_loader"   "$PYTHON_BIN test_gflare_loader.py"
add_task "test_regression_mr"   "$PYTHON_BIN test_regression_mr.py"
add_task "quick_testv2"         "$PYTHON_BIN quick_testv2.py"
add_task "quik_test"            "$PYTHON_BIN quik_test.py"
add_task "testing_space"        "$PYTHON_BIN testing_space.py"

# These are the real pipeline entrypoints.
# They are left direct on purpose so failures show the actual repo state.
add_task "trixel_brush_adapter" "$PYTHON_BIN trixel_brush_adapter.py data/brushes"
add_task "engine_debug_mr"      "$PYTHON_BIN engine_debug_mr.py data $OUT_ROOT/engine_debug"
add_task "trixel_demo_mr"       "$PYTHON_BIN trixel_demo_mr.py data $OUT_ROOT/trixel_demo"
add_task "world_tree_mr"        "$PYTHON_BIN world_tree_mr.py data $OUT_ROOT/world_tree"
add_task "stress_scene_mr"      "$PYTHON_BIN stress_scene_mr.py data $OUT_ROOT/stress_scene"

printf "label\tstatus\texit_code\tlog_file\n" > "$STATUS_FILE"

run_task() {
    local label="$1"
    local cmd="$2"
    local log_file="$LOG_DIR/${label}.log"
    local rc=0
    local status="PASS"

    printf "\n[%s] %s\n" "$(date +%H:%M:%S)" "$label"
    printf "cmd: %s\n" "$cmd"

    if command -v timeout >/dev/null 2>&1; then
        (
            cd "$REPO_DIR" &&
            timeout --foreground "${TASK_TIMEOUT}s" bash -lc "$cmd"
        ) >"$log_file" 2>&1 || rc=$?
    else
        (
            cd "$REPO_DIR" &&
            bash -lc "$cmd"
        ) >"$log_file" 2>&1 || rc=$?
    fi

    case "$rc" in
        0)   status="PASS" ;;
        124) status="TIMEOUT" ;;
        *)   status="FAIL" ;;
    esac

    printf "%s\t%s\t%s\t%s\n" "$label" "$status" "$rc" "$log_file" >> "$STATUS_FILE"

    if [[ "$status" == "PASS" ]]; then
        printf "PASS  %s\n" "$label"
    else
        printf "%s  %s  (exit %s)\n" "$status" "$label" "$rc"
        printf -- "----- last 25 lines: %s -----\n" "$log_file"
        tail -n 25 "$log_file" || true
        printf -- "--------------------------------\n"
    fi
}

for i in "${!LABELS[@]}"; do
    run_task "${LABELS[$i]}" "${CMDS[$i]}"
done

pass_count=0
fail_count=0
timeout_count=0

printf "\nSummary\n"
printf "%-22s %-10s %-10s %s\n" "task" "status" "exit" "log"

while IFS=$'\t' read -r label status exit_code log_file; do
    [[ "$label" == "label" ]] && continue
    printf "%-22s %-10s %-10s %s\n" "$label" "$status" "$exit_code" "$log_file"
    case "$status" in
        PASS)    ((pass_count+=1)) ;;
        FAIL)    ((fail_count+=1)) ;;
        TIMEOUT) ((timeout_count+=1)) ;;
    esac
done < "$STATUS_FILE"

printf "\nOutput root: %s\n" "$OUT_ROOT"
printf "Latest link: %s\n" "/tmp/trixel_smoke_latest"
printf "Passed: %d  Failed: %d  Timed out: %d\n" "$pass_count" "$fail_count" "$timeout_count"

if (( fail_count > 0 || timeout_count > 0 )); then
    exit 1
fi

exit 0
