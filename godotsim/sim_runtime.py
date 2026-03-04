#!/usr/bin/env python3
"""
sim_runtime.py — SLIM entrypoint for EngAIn Runtime.

This file does exactly three things:
    1. Instantiates EngAInRuntime
    2. Injects it into RuntimeHTTPHandler
    3. Starts the HTTP server

All engine logic lives in runtime_core.py.
All HTTP routing lives in http_handlers.py.
All scene logic lives in scene_manager.py.
All command routing lives in command_dispatcher.py.
All vault utilities live in vault_manager.py.
"""

import os
import threading
import time
import inspect
from http.server import ThreadingHTTPServer

from runtime_core import EngAInRuntime
from http_handlers import RuntimeHTTPHandler


def main():
    print("=" * 50)
    print("  EngAIn Runtime Server")
    print("=" * 50)

    runtime = EngAInRuntime()
    RuntimeHTTPHandler.runtime = runtime

    # === SAFE: background sim pump (no engine coupling; method-discovery, no guessing) ===
    _stop_evt = threading.Event()

    def _pick_method(obj, preferred_names):
        for name in preferred_names:
            fn = getattr(obj, name, None)
            if callable(fn):
                try:
                    sig = inspect.signature(fn)
                except Exception:
                    return fn, 0  # can't inspect; call without args
                # Count required positional params excluding self
                params = [p for p in sig.parameters.values()
                          if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
                # bound method: self already bound, so 0 means call(), 1 means call(dt)
                if len(params) == 0:
                    return fn, 0
                if len(params) == 1:
                    return fn, 1
                # more than 1 positional arg: skip (we won't guess)
        return None, None

    _drain_fn, _drain_arity = _pick_method(runtime, [
        "process_commands",
        "drain_commands",
        "process_queue",
        "pump_commands",
        "run_commands",
        "apply_commands",
    ])

    _step_fn, _step_arity = _pick_method(runtime, [
        "step",
        "tick",
        "update",
        "pump",
        "advance",
    ])

    if _drain_fn is None and _step_fn is None:
        print("[PUMP] FATAL: No drain/step method found on EngAInRuntime.")
        print("[PUMP] Available methods containing step/tick/update/pump:")
        for n in dir(runtime):
            ln = n.lower()
            if any(k in ln for k in ("step", "tick", "update", "pump", "drain", "command")):
                print("  -", n)
    else:
        print("[PUMP] Using drain:", getattr(_drain_fn, "__name__", None), "arity:", _drain_arity)
        print("[PUMP] Using step :", getattr(_step_fn, "__name__", None), "arity:", _step_arity)

    def _pump_loop():
        target_hz = 60.0
        target_dt = 1.0 / target_hz
        last = time.time()
        print("[PUMP] Sim pump thread started @ 60Hz")
        while not _stop_evt.is_set():
            now = time.time()
            dt = now - last
            last = now
            # clamp dt so a hiccup doesn't create a giant physics jump
            if dt > 0.1:
                dt = 0.1

            try:
                if _drain_fn is not None:
                    if _drain_arity == 0:
                        _drain_fn()
                    else:
                        _drain_fn(dt)

                if _step_fn is not None:
                    if _step_arity == 0:
                        _step_fn()
                    else:
                        _step_fn(dt)

            except Exception as e:
                print(f"[PUMP] Error: {e}")
                time.sleep(0.1)

            time.sleep(target_dt)

    _pump_thread = threading.Thread(target=_pump_loop, daemon=True)
    _pump_thread.start()
    # === END SAFE PUMP ===

    server = ThreadingHTTPServer(("localhost", 8080), RuntimeHTTPHandler)

    print(f"\nServer running on http://localhost:8080 (Multi-threaded)")
    print("Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        _stop_evt.set()
        runtime.shutdown()
        server.shutdown()
        print("Goodbye!")


if __name__ == "__main__":
    main()
