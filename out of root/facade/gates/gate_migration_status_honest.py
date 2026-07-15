# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/facade/gates/gate_migration_status_honest.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


VALID_STATUSES = {"in_progress", "not_started", "partial", "complete"}


def gate_migration_status_honest(packet: dict[str, Any]) -> GateResult:
    """Validate migration status is honest."""
    migration_status = packet.get("migration_status")

    if not isinstance(migration_status, dict):
        return GateResult(
            "gate_migration_status_honest",
            "FALSE",
            "migration_status must be a dict",
        )

    status = migration_status.get("status")
    if status not in VALID_STATUSES:
        return GateResult(
            "gate_migration_status_honest",
            "FALSE",
            f"Invalid migration status: {status}",
        )

    if not isinstance(migration_status.get("legacy_source_active"), bool):
        return GateResult(
            "gate_migration_status_honest",
            "FALSE",
            "legacy_source_active must be boolean",
        )

    if not isinstance(migration_status.get("full_migration_complete"), bool):
        return GateResult(
            "gate_migration_status_honest",
            "FALSE",
            "full_migration_complete must be boolean",
        )

    # Honesty check: if legacy_source_active is True, full_migration_complete must be False
    if migration_status.get("legacy_source_active") and migration_status.get("full_migration_complete"):
        return GateResult(
            "gate_migration_status_honest",
            "FALSE",
            "HARD REJECT: claims full_migration_complete=True but legacy_source_active=True",
        )

    return GateResult(
        "gate_migration_status_honest",
        "TRUE",
        "Migration status is honest",
    )