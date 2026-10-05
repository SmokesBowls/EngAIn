#!/usr/bin/env fish
# Safe replacement; never execute the historical PID-only stop script.
set ROOT (path resolve (path dirname (status filename)))
python3 "$ROOT/tools/stop_stack_safe.py" --root "$ROOT"
exit $status
