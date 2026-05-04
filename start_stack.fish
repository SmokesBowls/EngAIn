#!/usr/bin/env fish

set ROOT "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn"
set RUNDIR "$ROOT/.run"
set LOGDIR "$ROOT/.logs"

mkdir -p "$RUNDIR"
mkdir -p "$LOGDIR"

function banner
    echo
    echo "=================================================="
    echo $argv[1]
    echo "=================================================="
end

# Guard: only run from Desktop project root
set EXPECT "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn"
set HERE (pwd -P)

if test "$HERE" != "$EXPECT"
    echo "[STOP] Wrong working dir:"
    echo "       HERE:   $HERE"
    echo "       EXPECT: $EXPECT"
    exit 1
end

function require_file
    if not test -f $argv[1]
        echo "[FAIL] Missing file: $argv[1]"
        exit 1
    end
end

function require_dir
    if not test -d $argv[1]
        echo "[FAIL] Missing directory: $argv[1]"
        exit 1
    end
end

function port_listening
    set port $argv[1]
    ss -ltnH | awk '{print $4}' | grep -Eq "(^|.*:)$port\$"
end

function start_bg
    set label $argv[1]
    set port $argv[2]
    set logfile $argv[3]
    set cmd $argv[4..-1]

    if port_listening $port
        echo "[SKIP] $label already listening on $port"
        return 0
    end

    echo "[START] $label"
    echo "        port: $port"
    echo "        log:  $logfile"
    echo -n "        cmd:"
    for part in $cmd
        echo -n " $part"
    end
    echo

    nohup $cmd > "$logfile" 2>&1 &
    set pid $last_pid
    echo $pid > "$RUNDIR/$label.pid"

    sleep 3

    if port_listening $port
        echo "[OK]   $label listening on $port (pid=$pid)"
        return 0
    end

    if ps -p $pid >/dev/null 2>/dev/null
        echo "[FAIL] $label is still running, but port $port is not listening"
    else
        echo "[FAIL] $label exited early"
    end

    if test -f "$logfile"
        echo
        echo "----- tail $logfile -----"
        tail -n 120 "$logfile"
        echo "-------------------------"
    end

    exit 1
end

function show_ports
    echo
    echo "[PORTS]"
    ss -ltnp | grep -E '(:8080|:8765|:8090)'; or true
end

banner "EngAIn full Python stack bring-up"

require_dir "$ROOT/godotsim"
require_dir "$ROOT/godotengain/engainos"

require_file "$ROOT/godotsim/sim_runtime.py"
require_file "$ROOT/godotengain/engainos/launch_engine.py"
require_file "$ROOT/godotengain/engainos/engainos_server.py"

banner "Checking local tools"

for cmd in python3 ss awk grep
    if not command -q $cmd
        echo "[FAIL] Missing command: $cmd"
        exit 1
    end
end

python3 -c "import uvicorn, fastapi" >/dev/null 2>&1
if test $status -ne 0
    echo "[FAIL] Missing Python modules: uvicorn and/or fastapi"
    echo "Install with:"
    echo "  sudo pacman -S uvicorn python-fastapi"
    exit 1
end

echo "[OK] python3, ss, awk, grep, uvicorn, fastapi found"

banner "Starting sim_runtime.py"
cd "$ROOT/godotsim"; or exit 1
start_bg "sim_runtime" "8080" "$LOGDIR/sim_runtime.log" python3 -u sim_runtime.py

banner "Starting launch_engine.py"
cd "$ROOT/godotengain/engainos"; or exit 1
start_bg "launch_engine" "8765" "$LOGDIR/launch_engine.log" python3 -u launch_engine.py

banner "Starting engainos_server uvicorn"
cd "$ROOT/godotengain/engainos"; or exit 1
start_bg "engainos_uvicorn" "8090" "$LOGDIR/engainos_uvicorn.log" python3 -m uvicorn engainos_server:app --host 127.0.0.1 --port 8090

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
