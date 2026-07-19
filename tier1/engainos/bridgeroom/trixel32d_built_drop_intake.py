"""Passive checksum-locked file-drop intake for Trixel built responses.

Clones the proven EngAIn boot file-drop pattern: one fixed-name envelope and
one fixed-name payload file per drop slot, and one fixed-path receipt whose
existence is the consume state of that slot (identity semantics — no clock,
no expiration system, no second ledger).

Byte identity is SHA-256 over the raw built-response payload file bytes,
excluding the transport envelope, filename, and filesystem metadata. Intake
verifies that checksum against both the envelope declaration and the trusted
expected identity BEFORE parsing the payload. Parsing and identity/policy
validation then reuse the existing byte-level built-response machinery
unchanged. This intake authorizes no collision, no runtime execution, no
scene attachment, and no world mutation.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.gates.gate_trixel32d_handshake import (
    BuiltSurfaceValidation,
    validate_trixel32d_surface_built_bytes,
)

DROP_CONTRACT = "engainos.trixel32d_built_drop.v1"
DROP_PACKET_TYPE = "trixel32d_built_drop"
RECEIPT_CONTRACT = "engainos.trixel32d_built_intake_receipt.v1"

ENVELOPE_FILENAME = "TRIXEL32D_SURFACE_BUILT_DROP_V1.json"
PAYLOAD_FILENAME = "TRIXEL32D_SURFACE_BUILT_PAYLOAD_V1.json"
RECEIPT_FILENAME = "TRIXEL32D_SURFACE_BUILT_INTAKE_V1.receipt.json"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_ENVELOPE_FIELDS = frozenset({
    "contract",
    "packet_type",
    "drop_id",
    "generated_by",
    "payload_file",
    "payload_sha256",
    "request_id",
    "surface_id",
    "topology_policy",
})


@dataclass(frozen=True)
class IntakeResult:
    """Result of one fail-closed drop intake."""

    errors: tuple[str, ...]
    validation: BuiltSurfaceValidation | None
    receipt: Any

    @property
    def accepted(self) -> bool:
        return not self.errors and self.validation is not None


def write_built_drop(
    drop_dir: str | Path,
    payload_bytes: bytes,
    *,
    generated_by: str,
    request_id: str,
    surface_id: str,
    topology_policy: str,
) -> dict[str, Any]:
    """Write one drop: exact payload bytes plus the declaring envelope."""
    directory = Path(drop_dir)
    directory.mkdir(parents=True, exist_ok=True)
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    envelope = {
        "contract": DROP_CONTRACT,
        "packet_type": DROP_PACKET_TYPE,
        "drop_id": f"t32ddrop_{payload_sha256[:16]}",
        "generated_by": generated_by,
        "payload_file": PAYLOAD_FILENAME,
        "payload_sha256": payload_sha256,
        "request_id": request_id,
        "surface_id": surface_id,
        "topology_policy": topology_policy,
    }
    (directory / PAYLOAD_FILENAME).write_bytes(payload_bytes)
    (directory / ENVELOPE_FILENAME).write_text(
        json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8"
    )
    return envelope


def intake_built_drop(
    drop_dir: str | Path,
    *,
    trusted_request: Any,
    expected_payload_sha256: str,
    expected_topology_policy: str,
    receipt_path: str | Path,
) -> IntakeResult:
    """Consume one drop fail-closed. Rejection carries errors and nothing else."""
    errors: list[str] = []
    directory = Path(drop_dir)
    receipt_file = Path(receipt_path)

    if not isinstance(expected_payload_sha256, str) or _SHA256_PATTERN.fullmatch(
        expected_payload_sha256
    ) is None:
        return _rejected("expected_payload_sha256 must be 64 lowercase hexadecimal characters")
    if not isinstance(expected_topology_policy, str) or not expected_topology_policy:
        return _rejected("expected_topology_policy must be a non-empty string")

    if receipt_file.exists():
        return _rejected(
            "intake receipt already exists; this drop slot was consumed and a"
            " duplicate consume rejects"
        )

    envelope_path = directory / ENVELOPE_FILENAME
    if not envelope_path.is_file():
        return _rejected(f"drop envelope is missing: {ENVELOPE_FILENAME}")
    try:
        envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return _rejected(f"drop envelope could not be parsed: {type(exc).__name__}")
    if not isinstance(envelope, dict):
        return _rejected("drop envelope must be a JSON object")
    unknown = sorted(set(envelope.keys()) - _ENVELOPE_FIELDS)
    if unknown:
        return _rejected(f"drop envelope contains undeclared keys: {', '.join(unknown)}")
    missing = sorted(_ENVELOPE_FIELDS - set(envelope.keys()))
    if missing:
        return _rejected(f"drop envelope is missing required keys: {', '.join(missing)}")
    if envelope.get("contract") != DROP_CONTRACT:
        return _rejected(f"drop envelope contract must be '{DROP_CONTRACT}'")
    if envelope.get("packet_type") != DROP_PACKET_TYPE:
        return _rejected(f"drop envelope packet_type must be '{DROP_PACKET_TYPE}'")
    if envelope.get("payload_file") != PAYLOAD_FILENAME:
        return _rejected(f"drop envelope payload_file must be exactly '{PAYLOAD_FILENAME}'")

    declared_sha256 = envelope.get("payload_sha256")
    if not isinstance(declared_sha256, str) or _SHA256_PATTERN.fullmatch(declared_sha256) is None:
        return _rejected("drop envelope payload_sha256 must be 64 lowercase hexadecimal characters")
    if declared_sha256 != expected_payload_sha256:
        return _rejected(
            "drop is stale: envelope payload_sha256 does not match the currently"
            " expected payload identity"
        )
    if envelope.get("drop_id") != f"t32ddrop_{declared_sha256[:16]}":
        return _rejected("drop envelope drop_id must derive from the payload checksum")

    payload_path = directory / PAYLOAD_FILENAME
    if not payload_path.is_file():
        return _rejected(f"drop payload is missing: {PAYLOAD_FILENAME}")
    payload_bytes = payload_path.read_bytes()
    actual_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    if actual_sha256 != declared_sha256:
        return _rejected(
            "drop payload bytes do not match the declared checksum: "
            f"expected {declared_sha256}, got {actual_sha256}"
        )

    validation = validate_trixel32d_surface_built_bytes(
        payload_bytes,
        trusted_request,
        expected_response_sha256=expected_payload_sha256,
    )
    if not validation.accepted:
        first = validation.errors[0] if validation.errors else "unknown rejection"
        return _rejected(f"drop payload failed built-response validation: {first}")
    packet = validation.packet
    assert packet is not None

    if packet.get("status") != "BUILT":
        return _rejected("drop payload must be a BUILT response")
    for field in ("request_id", "surface_id", "topology_policy"):
        if envelope.get(field) != packet.get(field):
            return _rejected(
                f"drop envelope {field} does not match the validated payload;"
                " a misdeclaring envelope rejects"
            )
    if packet.get("topology_policy") != expected_topology_policy:
        return _rejected(
            "drop payload topology_policy is not the authorized"
            f" '{expected_topology_policy}' payload"
        )

    receipt = MappingProxyType({
        "contract": RECEIPT_CONTRACT,
        "drop_id": envelope["drop_id"],
        "payload_sha256": actual_sha256,
        "request_id": packet["request_id"],
        "surface_id": packet["surface_id"],
        "topology_policy": packet["topology_policy"],
        "status": "INTAKE_ACCEPTED",
        "collision_authorized": False,
        "godot_runtime_executed": False,
        "scene_attached": False,
        "world_mutated": False,
        "runtime_quarantine_changed": False,
    })
    return IntakeResult(errors=(), validation=validation, receipt=receipt)


def write_intake_receipt(receipt_path: str | Path, result: IntakeResult) -> Path:
    """Persist the receipt for one accepted intake; never overwrite."""
    if not result.accepted or result.receipt is None:
        raise ValueError("only an accepted intake writes a receipt")
    receipt_file = Path(receipt_path)
    if receipt_file.exists():
        raise FileExistsError(
            "intake receipt already exists; refusing duplicate receipt write"
        )
    receipt_file.parent.mkdir(parents=True, exist_ok=True)
    receipt_file.write_text(
        json.dumps(dict(result.receipt), indent=2, sort_keys=True), encoding="utf-8"
    )
    return receipt_file


def _rejected(message: str) -> IntakeResult:
    return IntakeResult(errors=(message,), validation=None, receipt=None)
