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
from http.server import ThreadingHTTPServer

from runtime_core import EngAInRuntime
from http_handlers import RuntimeHTTPHandler


def main():
    print("=" * 50)
    print("  EngAIn Runtime Server")
    print("=" * 50)

    runtime = EngAInRuntime()
    RuntimeHTTPHandler.runtime = runtime

    server = ThreadingHTTPServer(("localhost", 8080), RuntimeHTTPHandler)

    print(f"\nServer running on http://localhost:8080 (Multi-threaded)")
    print("Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        runtime.shutdown()
        server.shutdown()
        print("Goodbye!")


if __name__ == "__main__":
    main()
