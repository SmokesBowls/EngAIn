"""Public facade. Do not place implementation here yet. Legacy source remains in godotsim/sim_runtime.py.

Safety: this module intentionally avoids importing godotsim.sim_runtime because that legacy entrypoint can start server/runtime side effects when executed in deployment workflows.
"""

LEGACY_ENTRYPOINT = "godotsim/sim_runtime.py"
RUNTIME_API_PORT = 8080


def not_imported_reason() -> str:
    return (
        "engain.runtime.sim intentionally does not import godotsim.sim_runtime; "
        "that file is an operational entrypoint."
    )
