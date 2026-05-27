#!/usr/bin/env fish

set ROOT "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn"
set RUNDIR "$ROOT/.run"

function stop_pidfile
    set name $argv[1]
    set pidfile "$RUNDIR/$name.pid"

    if test -f "$pidfile"
        set pid (cat "$pidfile")

        if test -n "$pid"
            if ps -p $pid >/dev/null 2>/dev/null
                echo "[STOP] $name pid=$pid"
                kill $pid
            else
                echo "[SKIP] $name pid file exists but process is already gone"
            end
        end

        rm -f "$pidfile"
    else
        echo "[SKIP] No pid file for $name"
    end
end

stop_pidfile "sim_runtime"
stop_pidfile "launch_engine"
stop_pidfile "engainos_uvicorn"
stop_pidfile "tile_server"

echo
echo "[PORTS AFTER STOP]"
ss -ltnp | grep -E '(:8080|:8765|:8090|:8766)' || true

