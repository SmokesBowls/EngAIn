#!/usr/bin/env python3
"""Passive stitched-payload transport proof runner (TRIXEL32D_BUILT_DROP_INTAKE_PROOF_V1).

Writes the real checksum-locked drop from the vendored stitched built-response
bytes, consumes it through intake, executes the existing apply-authorization
gate, and persists the receipt. Authorized for this proof only: no Godot
runtime execution, scene attachment, placement, collision allocation, world
mutation, or runtime-quarantine change.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tier1.engainos.bridgeroom.trixel32d_built_drop_intake import (
    RECEIPT_FILENAME,
    intake_built_drop,
    write_built_drop,
    write_intake_receipt,
)
from tier1.engainos.gates.gate_trixel32d_surface_apply import gate_trixel32d_surface_apply
from tier1.engainos.tests.test_trixel32d_built_drop_intake import (
    CONNECTED_PAYLOAD,
    CONNECTED_REQUEST,
    CONNECTED_SHA256,
    REQUEST_ID,
    STITCHED_POLICY,
    STITCHED_SURFACE_ID,
    stitched_apply_packet,
)
from tier1.engainos.tests.test_trixel32d_surface_apply import (
    authority_for,
    canonical_scene_truth,
)

DROP_DIR = ROOT / "runtime" / "trixel32d_built_drops"
RECEIPT_PATH = ROOT / "runtime" / "trixel32d_reports" / RECEIPT_FILENAME


def main() -> int:
    tag = "[trixel32d_built_drop_intake_proof]"
    envelope = write_built_drop(
        DROP_DIR,
        CONNECTED_PAYLOAD,
        generated_by="trixel3.2d",
        request_id=REQUEST_ID,
        surface_id=STITCHED_SURFACE_ID,
        topology_policy=STITCHED_POLICY,
    )
    print(f"{tag}[DROP_WRITTEN] {DROP_DIR} payload_sha256={envelope['payload_sha256']}")

    if RECEIPT_PATH.exists():
        print(f"{tag}[DUPLICATE_GUARD] receipt already exists; refusing re-consume")
        return 1

    result = intake_built_drop(
        DROP_DIR,
        trusted_request=CONNECTED_REQUEST,
        expected_payload_sha256=CONNECTED_SHA256,
        expected_topology_policy=STITCHED_POLICY,
        receipt_path=RECEIPT_PATH,
    )
    if not result.accepted:
        print(f"{tag}[INTAKE_REJECTED] {result.errors[0]}")
        return 1
    print(f"{tag}[INTAKE_ACCEPTED] surface_id={result.receipt['surface_id']}")

    packet = stitched_apply_packet()
    outcome = gate_trixel32d_surface_apply(
        packet,
        built_validation=result.validation,
        authority=authority_for(packet),
        scene_truth=canonical_scene_truth(),
    )
    print(f"{tag}[APPLY_GATE] {outcome.passed}: {outcome.message}")
    if not outcome.is_true():
        return 1

    receipt_file = write_intake_receipt(RECEIPT_PATH, result)
    print(f"{tag}[RECEIPT_WRITTEN] {receipt_file}")
    print(f"{tag}[COLLISION_AUTHORIZED] false (T_JUNCTION_WALL_EDGES limitation)")
    print(f"{tag}[GODOT_RUNTIME_EXECUTED] false")
    print(f"{tag}[RUNTIME_QUARANTINE_CHANGED] false")
    print(f"{tag}[PAYLOAD_SHA256] {hashlib.sha256(CONNECTED_PAYLOAD).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
