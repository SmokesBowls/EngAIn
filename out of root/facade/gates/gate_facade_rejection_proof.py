# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/facade/gates/gate_facade_rejection_proof.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult
from facade.gates.gate_no_side_effect_imports import gate_no_side_effect_imports
from facade.gates.gate_no_render_truth_mixed import gate_no_render_truth_mixed
from facade.gates.gate_migration_status_honest import gate_migration_status_honest
from facade.gates.gate_legacy_wrapped_not_replaced import gate_legacy_wrapped_not_replaced
from facade.gates.gate_no_runtime_entrypoint_import import gate_no_runtime_entrypoint_import


VALID_BASE_PACKET: dict[str, Any] = {
    "contract": "facade.witness_packet.v1",
    "source": "facade_witness",
    "authority_tier": "TIER_0_5",
    "authority_lane": "boundary_guard",
    "import_attempts": [
        {
            "module": "engainos.core.ap_core",
            "side_effects_checked": True,
            "passed": True,
        }
    ],
    "packet_validations": [
        {
            "packet_type": "godotsim.spatial_sim_packet.v1",
            "shape_valid": True,
        }
    ],
    "migration_status": {
        "status": "in_progress",
        "legacy_source_active": True,
        "full_migration_complete": False,
    },
    "legacy_wrapped": [
        {
            "module": "godotengain.engainos.core.ap_core",
            "wrapped": True,
            "replaced": False,
        }
    ],
    "runtime_entrypoints_guarded": [
        {
            "entrypoint": "launch_engine",
            "not_imported_by_design": True,
        }
    ],
}


BAD_PACKET_WITH_SIDE_EFFECT: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "import_attempts": [
        {
            "module": "engainos.core.ap_core",
            "side_effects_checked": True,
            "has_side_effects": True,
            "passed": True,
        }
    ],
}


BAD_PACKET_WITH_RENDER_TRUTH: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "render": True,
}


BAD_PACKET_LYING_ABOUT_MIGRATION: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "migration_status": {
        "status": "complete",
        "legacy_source_active": True,
        "full_migration_complete": True,
    },
}


BAD_PACKET_REPLACING_LEGACY: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "legacy_wrapped": [
        {
            "module": "godotengain.engainos.core.ap_core",
            "wrapped": True,
            "replaced": True,
        }
    ],
}


BAD_PACKET_IMPORTING_RUNTIME_ENTRYPOINT: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "runtime_entrypoints_guarded": [
        {
            "entrypoint": "launch_engine",
            "not_imported_by_design": False,
        }
    ],
}


def gate_rejects_side_effect(packet: dict[str, Any]) -> GateResult:
    """PROOF: Packet with side effects is rejected."""
    result = gate_no_side_effect_imports(BAD_PACKET_WITH_SIDE_EFFECT)

    if result.passed == "FALSE":
        return GateResult(
            "gate_rejects_side_effect",
            "TRUE",
            "Packet with side effects was correctly rejected",
        )

    return GateResult(
        "gate_rejects_side_effect",
        "FALSE",
        f"Packet with side effects should have been rejected but got {result.passed}: {result.message}",
    )


def gate_rejects_render_truth(packet: dict[str, Any]) -> GateResult:
    """PROOF: Packet with render truth is rejected."""
    result = gate_no_render_truth_mixed(BAD_PACKET_WITH_RENDER_TRUTH)

    if result.passed == "FALSE":
        return GateResult(
            "gate_rejects_render_truth",
            "TRUE",
            "Packet with render truth was correctly rejected",
        )

    return GateResult(
        "gate_rejects_render_truth",
        "FALSE",
        f"Packet with render truth should have been rejected but got {result.passed}: {result.message}",
    )


def gate_rejects_migration_lie(packet: dict[str, Any]) -> GateResult:
    """PROOF: Packet lying about migration status is rejected."""
    result = gate_migration_status_honest(BAD_PACKET_LYING_ABOUT_MIGRATION)

    if result.passed == "FALSE":
        return GateResult(
            "gate_rejects_migration_lie",
            "TRUE",
            "Packet lying about migration was correctly rejected",
        )

    return GateResult(
        "gate_rejects_migration_lie",
        "FALSE",
        f"Packet lying about migration should have been rejected but got {result.passed}: {result.message}",
    )


def gate_rejects_legacy_replacement(packet: dict[str, Any]) -> GateResult:
    """PROOF: Packet replacing legacy is rejected."""
    result = gate_legacy_wrapped_not_replaced(BAD_PACKET_REPLACING_LEGACY)

    if result.passed == "FALSE":
        return GateResult(
            "gate_rejects_legacy_replacement",
            "TRUE",
            "Packet replacing legacy was correctly rejected",
        )

    return GateResult(
        "gate_rejects_legacy_replacement",
        "FALSE",
        f"Packet replacing legacy should have been rejected but got {result.passed}: {result.message}",
    )


def gate_rejects_runtime_entrypoint_import(packet: dict[str, Any]) -> GateResult:
    """PROOF: Packet importing a runtime entrypoint without guarding is rejected."""
    result = gate_no_runtime_entrypoint_import(BAD_PACKET_IMPORTING_RUNTIME_ENTRYPOINT)

    if result.passed == "FALSE":
        return GateResult(
            "gate_rejects_runtime_entrypoint_import",
            "TRUE",
            "Packet importing runtime entrypoint was correctly rejected",
        )

    return GateResult(
        "gate_rejects_runtime_entrypoint_import",
        "FALSE",
        f"Packet importing runtime entrypoint should have been rejected but got {result.passed}: {result.message}",
    )