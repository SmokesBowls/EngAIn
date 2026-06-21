"""Safe EngAInOS runtime-server wrapper scaffold.

This module defines the future lawful port-8080 wrapper contract only. It is
intentionally importable without side effects:
  - no socket binding
  - no server startup
  - no direct scene/vault/world mutation
  - no direct AP runtime execution

Future implementation must route mutating HTTP surfaces through the EngAInOS
runtime gateway and AP runtime relay boundaries declared below. This scaffold is
not a live server and is not executable as an entrypoint.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any, Literal

RouteStatus = Literal["allowed", "blocked", "allowed_preflight_only"]


@dataclass(frozen=True)
class RouteContract:
    """Static contract for one future HTTP route."""

    route: str
    status: RouteStatus
    requires_gateway: bool
    requires_ap_relay: bool
    requires_schema_validation: bool
    mutation_surface: str
    direct_mutation_forbidden: bool
    allowed_after: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ROUTE_CONTRACTS: tuple[RouteContract, ...] = (
    RouteContract(
        route="/command",
        status="allowed_preflight_only",
        requires_gateway=True,
        requires_ap_relay=True,
        requires_schema_validation=True,
        mutation_surface="entity/world/action dispatch; may include AP runtime messages",
        direct_mutation_forbidden=True,
        allowed_after="RuntimeGateway accepts request and APRuntimeRelay validates/forwards AP messages without manufacturing authority flags.",
        notes="Read-only commands may be classified by RuntimeGateway, but wrapper must still schema-normalize before dispatch.",
    ),
    RouteContract(
        route="/snapshot",
        status="allowed",
        requires_gateway=False,
        requires_ap_relay=False,
        requires_schema_validation=True,
        mutation_surface="read-only snapshot export",
        direct_mutation_forbidden=True,
        allowed_after="Read-only response schema is validated and route contains no state mutation side effects.",
        notes="May read runtime snapshot only; must not hydrate by mutating canonical state during response.",
    ),
    RouteContract(
        route="/scene/load",
        status="blocked",
        requires_gateway=True,
        requires_ap_relay=True,
        requires_schema_validation=True,
        mutation_surface="scene state activation/load",
        direct_mutation_forbidden=True,
        allowed_after="EngAInOS gateway approves actor/reality/scene authority and AP relay accepts any AP/rule side effects.",
        notes="Must not call the scene manager's scene-load API directly from HTTP transport.",
    ),
    RouteContract(
        route="/vault/link",
        status="blocked",
        requires_gateway=True,
        requires_ap_relay=True,
        requires_schema_validation=True,
        mutation_surface="vault registry/link state and scene registry population",
        direct_mutation_forbidden=True,
        allowed_after="Gateway validates authority and schema/path anchors; relay covers AP rule/timeline consequences if any.",
        notes="Must not call the vault linker's link API directly from HTTP transport.",
    ),
    RouteContract(
        route="/vault/status",
        status="allowed",
        requires_gateway=False,
        requires_ap_relay=False,
        requires_schema_validation=True,
        mutation_surface="read-only vault status export",
        direct_mutation_forbidden=True,
        allowed_after="Read-only response schema is validated and no vault state is changed.",
        notes="Allowed as observation only; no implicit relink, scan, load, repair, or cache writes.",
    ),
    RouteContract(
        route="/world/sync",
        status="blocked",
        requires_gateway=True,
        requires_ap_relay=True,
        requires_schema_validation=True,
        mutation_surface="world build/sync/mirror/load side effects",
        direct_mutation_forbidden=True,
        allowed_after="Gateway accepts explicit authority; AP relay accepts rule/timeline intent; paths are anchored and dry-run/write mode is explicit.",
        notes="Must not build, mirror, chmod, rsync, bulk-load scenes, or write cache directly from HTTP transport.",
    ),
    RouteContract(
        route="/world/load_mirror",
        status="blocked",
        requires_gateway=True,
        requires_ap_relay=True,
        requires_schema_validation=True,
        mutation_surface="world mirror scene ingestion/load",
        direct_mutation_forbidden=True,
        allowed_after="Gateway accepts explicit authority and AP relay covers AP rule/timeline consequences before mirror load.",
        notes="Must not call the bulk scene-load API directly from HTTP transport.",
    ),
)

SAFE_RUNTIME_SERVER_WRAPPER_CONTRACT: dict[str, Any] = {
    "wrapper_file_path": "engainos/server/safe_runtime_server_entrypoint.py",
    "implementation_lane": "SAFE_SERVER_WRAPPER_IMPLEMENTATION_LANE",
    "status": "scaffold_only_not_live_server",
    "future_bind_host": "127.0.0.1",
    "future_bind_port": 8080,
    "server_runtime_lane": "BLOCKED",
    "port_8080_allowed": False,
    "auto_run_from_main": False,
    "side_effects_on_import": False,
    "authority_boundaries": {
        "runtime_gateway": "godotsim/godotsim_legacy/runtime_gateway.py",
        "ap_runtime_relay": "engainos/relays/ap_runtime_relay.py",
        "ap_runtime_direct_execution": "blocked",
    },
    "forbidden_direct_effects": (
        "socket_bind",
        "run_uvicorn",
        "instantiate_runtime_http_server",
        "direct_scene_mutation",
        "direct_vault_link",
        "direct_bulk_scene_load",
        "direct_timeline_write",
        "direct_rule_state_mutation",
    ),
}


def route_contracts_as_dicts() -> list[dict[str, Any]]:
    """Return a copy-safe list of route contract dictionaries."""

    return [contract.to_dict() for contract in ROUTE_CONTRACTS]


def build_safe_runtime_server_preflight(
    *,
    include_route_contracts: bool = True,
    include_forbidden_effects: bool = True,
) -> dict[str, Any]:
    """Build the scaffold preflight report for the future safe server wrapper.

    This function is pure data assembly. It does not import runtime systems, bind
    sockets, instantiate servers, load scenes, link vaults, or write timeline
    state.
    """

    contract = deepcopy(SAFE_RUNTIME_SERVER_WRAPPER_CONTRACT)
    mutating_route_errors: dict[str, list[str]] = {}
    read_only_route_errors: dict[str, list[str]] = {}

    for route in ROUTE_CONTRACTS:
        if route.route in {"/command", "/scene/load", "/vault/link", "/world/sync", "/world/load_mirror"}:
            errors: list[str] = []
            if not route.requires_gateway:
                errors.append("missing_gateway_requirement")
            if not route.requires_ap_relay:
                errors.append("missing_ap_relay_requirement")
            if route.status == "allowed":
                errors.append("mutating_route_live_allowed_in_scaffold")
            if not route.direct_mutation_forbidden:
                errors.append("direct_mutation_not_forbidden")
            if errors:
                mutating_route_errors[route.route] = errors
        elif route.route in {"/snapshot", "/vault/status"}:
            errors = []
            if route.status != "allowed":
                errors.append("read_only_route_not_allowed")
            if route.requires_gateway:
                errors.append("read_only_route_requires_gateway")
            if route.requires_ap_relay:
                errors.append("read_only_route_requires_ap_relay")
            if not route.direct_mutation_forbidden:
                errors.append("read_only_direct_mutation_not_forbidden")
            if errors:
                read_only_route_errors[route.route] = errors

    preflight: dict[str, Any] = {
        "SAFE_SERVER_WRAPPER_IMPLEMENTATION_LANE": True,
        "SAFE_SERVER_WRAPPER_SCAFFOLD_ONLY": True,
        "SAFE_SERVER_ENTRYPOINT_IDENTIFIED": False,
        "SERVER_RUNTIME_LANE": "BLOCKED",
        "PORT_8080_ALLOWED": False,
        "import_side_effects_expected": False,
        "route_contract_count": len(ROUTE_CONTRACTS),
        "mutating_route_errors": mutating_route_errors,
        "read_only_route_errors": read_only_route_errors,
        "route_contracts_valid": not mutating_route_errors and not read_only_route_errors,
    }

    if include_route_contracts:
        preflight["route_contracts"] = route_contracts_as_dicts()
    if include_forbidden_effects:
        preflight["forbidden_direct_effects"] = list(contract["forbidden_direct_effects"])

    preflight["contract"] = contract
    return preflight
