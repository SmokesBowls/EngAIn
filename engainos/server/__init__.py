"""EngAInOS safe server wrapper package.

This package is a scaffold for future lawful port-8080 runtime exposure.
Importing it must not start servers, bind sockets, or mutate runtime state.
"""

from .safe_runtime_server_entrypoint import (
    ROUTE_CONTRACTS,
    SAFE_RUNTIME_SERVER_WRAPPER_CONTRACT,
    build_safe_runtime_server_preflight,
)

__all__ = [
    "ROUTE_CONTRACTS",
    "SAFE_RUNTIME_SERVER_WRAPPER_CONTRACT",
    "build_safe_runtime_server_preflight",
]
