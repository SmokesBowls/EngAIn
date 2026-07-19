"""EngAInOS dispatcher for checksum-locked surface-request file drops.

Clones the boot file-drop pattern on the request side: one fixed-name
envelope and payload per drop slot. The dispatcher validates the request
bytes semantically through the existing request validator before writing;
a request that fails validation dispatches nothing. The payload file
carries the exact submitted bytes — the dispatcher never re-serializes.
Passive: writes the drop and nothing else.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.gates.gate_trixel32d_handshake import (
    validate_trixel32d_surface_request,
)

REQUEST_DROP_CONTRACT = "engainos.trixel32d_request_drop.v1"
REQUEST_DROP_PACKET_TYPE = "trixel32d_request_drop"
REQUEST_ENVELOPE_FILENAME = "TRIXEL32D_SURFACE_REQUEST_DROP_V1.json"
REQUEST_PAYLOAD_FILENAME = "TRIXEL32D_SURFACE_REQUEST_PAYLOAD_V1.json"


@dataclass(frozen=True)
class DispatchResult:
    errors: tuple[str, ...]
    envelope: Any

    @property
    def dispatched(self) -> bool:
        return not self.errors and self.envelope is not None


def dispatch_request_drop(
    drop_dir: str | Path,
    request_bytes: bytes,
    *,
    generated_by: str,
) -> DispatchResult:
    """Validate then write one request drop; rejection writes nothing."""
    if not isinstance(request_bytes, bytes) or not request_bytes:
        return _rejected("request_bytes must be non-empty bytes")
    if not isinstance(generated_by, str) or not generated_by:
        return _rejected("generated_by must be a non-empty string")

    directory = Path(drop_dir)
    if (directory / REQUEST_ENVELOPE_FILENAME).exists():
        return _rejected(
            "request drop envelope already exists; this drop slot was dispatched"
            " and a duplicate dispatch rejects"
        )

    try:
        request = json.loads(request_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        return _rejected(f"request bytes could not be parsed: {type(exc).__name__}")

    validation_errors = validate_trixel32d_surface_request(request)
    if validation_errors:
        return _rejected(f"request failed validation: {validation_errors[0]}")

    request_id = request["identity"]["request_id"]
    topology_policy = request["construction"]["topology_policy"]
    payload_sha256 = hashlib.sha256(request_bytes).hexdigest()
    envelope = {
        "contract": REQUEST_DROP_CONTRACT,
        "packet_type": REQUEST_DROP_PACKET_TYPE,
        "drop_id": f"t32ddrop_{payload_sha256[:16]}",
        "generated_by": generated_by,
        "payload_file": REQUEST_PAYLOAD_FILENAME,
        "payload_sha256": payload_sha256,
        "request_id": request_id,
        "topology_policy": topology_policy,
    }
    directory.mkdir(parents=True, exist_ok=True)
    (directory / REQUEST_PAYLOAD_FILENAME).write_bytes(request_bytes)
    (directory / REQUEST_ENVELOPE_FILENAME).write_text(
        json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8"
    )
    return DispatchResult(errors=(), envelope=envelope)


def _rejected(message: str) -> DispatchResult:
    return DispatchResult(errors=(message,), envelope=None)
