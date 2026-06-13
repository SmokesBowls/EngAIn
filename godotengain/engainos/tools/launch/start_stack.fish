#!/usr/bin/env fish

set ROOT "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn"
set RUNDIR "$ROOT/.run"
set LOGDIR "$ROOT/.logs"

mkdir -p "$RUNDIR" "$LOGDIR"

function banner
    echo
    echo "=================================================="
    echo $argv[1]
    echo "=================================================="
end

function require_file
    if not test -f $argv[1]
        echo "[FAIL] Missing file: $argv[1]"
        exit 1
    end
end

function start_bg
    set label $argv[1]
    set logfile $argv[2]
    set cmd $argv[3..-1]

    echo "[START] $label"
    echo "        log: $logfile"
    echo -n "        cmd:"
    for part in $cmd
        echo -n " $part"
    end
    echo

    nohup $cmd >"$logfile" 2>&1 &
    set pid $last_pid
    echo $pid > "$RUNDIR/$label.pid"

    sleep 3

    if not ps -p $pid >/dev/null
        echo "[FAIL] $label exited early"
        if test -f "$logfile"
            echo
            echo "----- tail $logfile -----"
            tail -n 80 "$logfile"
            echo "-------------------------"
        end
        exit 1
    end

    echo "[OK]   $label pid=$pid"
end

function show_ports
    echo
    echo "[PORTS]"
    ss -ltnp | grep -E '(:8080|:8765|:8090)'
end

banner "EngAIn full Python stack bring-up"

require_file "$ROOT/godotsim/sim_runtime.py"
require_file "$ROOT/godotengain/engainos/launch_engine.py"
require_file "$ROOT/godotengain/engainos/engainos_server.py"

for cmd in python3 ss
    if not command -q $cmd
        echo "[FAIL] Missing command: $cmd"
        exit 1
    end
end

python3 -c "import uvicorn, fastapi" >/dev/null 2>&1
if test $status -ne 0
    echo "[FAIL] Missing Python modules: uvicorn and/or fastapi"
    echo "Install with:"
    echo "  python3 -m pip install uvicorn fastapi"
    exit 1
end

banner "Starting sim_runtime.py"
cd "$ROOT/godotsim"; or exit 1
start_bg "sim_runtime" "$LOGDIR/sim_runtime.log" python3 sim_runtime.py

banner "Starting launch_engine.py"
cd "$ROOT/godotengain/engainos"; or exit 1
start_bg "launch_engine" "$LOGDIR/launch_engine.log" python3 launch_engine.py

banner "Starting engainos_server uvicorn"
cd "$ROOT/godotengain/engainos"; or exit 1
start_bg "engainos_uvicorn" "$LOGDIR/engainos_uvicorn.log" python3 -m uvicorn engainos_server:app --host 127.0.0.1 --port 8090

banner "Live port check"
show_ports

echo
echo "[DONE] Full Python stack launch attempted."
echo
echo "Logs:"
echo "  $LOGDIR/sim_runtime.log"
echo "  $LOGDIR/launch_engine.log"
echo "  $LOGDIR/engainos_uvicorn.log"
echo
echo "PIDs:"
echo "  $RUNDIR/sim_runtime.pid"
echo "  $RUNDIR/launch_engine.pid"
echo "  $RUNDIR/engainos_uvicorn.pid"
