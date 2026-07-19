#!/usr/bin/env python3
"""Complete-edge passive transport loop proof (TRIXEL32D_COMPLETE_EDGE_LOOP_PROOF_V1).

Same passive chain as the stitched loop proof, for the accepted complete-edge
payload, on new unoccupied slots provided by the existing slot-identity
mechanism: each slot is an identity-keyed subdirectory named by the
checksum-derived drop_id, with the fixed envelope/payload/receipt filenames
inside it. Prior live drops and receipts are never cleared, moved,
overwritten, renamed, or deleted; occupied slots refuse. No Godot runtime
execution, scene attachment, placement, collision allocation, world mutation,
or runtime-quarantine change.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tier1.engainos.bridgeroom.trixel32d_request_dispatch import (
    REQUEST_ENVELOPE_FILENAME,
    dispatch_request_drop,
)
from tier1.engainos.bridgeroom.trixel32d_built_drop_intake import (
    ENVELOPE_FILENAME as RESPONSE_ENVELOPE_FILENAME,
    RECEIPT_FILENAME,
    intake_built_drop,
    write_intake_receipt,
)
from tier1.engainos.gates.gate_trixel32d_surface_apply import gate_trixel32d_surface_apply
from tier1.engainos.tests.test_trixel32d_complete_edge_transport import (
    COMPLETE_EDGE_POLICY,
    COMPLETE_EDGE_REQUEST,
    COMPLETE_EDGE_REQUEST_BYTES,
    COMPLETE_EDGE_SHA256,
    REQUEST_ID,
    complete_edge_apply_packet,
)
from tier1.engainos.tests.test_trixel32d_surface_apply import (
    authority_for,
    canonical_scene_truth,
)

REQUEST_SLOT_ID = "t32ddrop_" + hashlib.sha256(COMPLETE_EDGE_REQUEST_BYTES).hexdigest()[:16]
RESPONSE_SLOT_ID = "t32ddrop_" + COMPLETE_EDGE_SHA256[:16]
REQUEST_DIR = ROOT / "runtime" / "trixel32d_requests" / REQUEST_SLOT_ID
RESPONSE_DIR = ROOT / "runtime" / "trixel32d_built_drops" / RESPONSE_SLOT_ID
RECEIPT_PATH = ROOT / "runtime" / "trixel32d_reports" / RESPONSE_SLOT_ID / RECEIPT_FILENAME
TRIXEL_TOOL = ROOT.parent / "trixel3.2d" / "tools" / "consume_trixel32d_request_drop.py"


def main() -> int:
    tag = "[trixel32d_complete_edge_loop_proof]"
    print(f"{tag}[REQUEST_SLOT] {REQUEST_SLOT_ID}")
    print(f"{tag}[RESPONSE_SLOT] {RESPONSE_SLOT_ID}")

    for occupied, label in (
        (REQUEST_DIR / REQUEST_ENVELOPE_FILENAME, "request drop slot"),
        (RESPONSE_DIR / RESPONSE_ENVELOPE_FILENAME, "response drop slot"),
        (RECEIPT_PATH, "intake receipt slot"),
    ):
        if occupied.exists():
            print(f"{tag}[SLOT_OCCUPIED] {label}: {occupied}")
            print(f"{tag}[REFUSED] occupied slots refuse; no prior artifact is touched")
            return 1

    dispatch = dispatch_request_drop(REQUEST_DIR, COMPLETE_EDGE_REQUEST_BYTES, generated_by="engainos")
    if not dispatch.dispatched:
        print(f"{tag}[DISPATCH_REJECTED] {dispatch.errors[0]}")
        return 1
    print(f"{tag}[REQUEST_DISPATCHED] sha256={dispatch.envelope['payload_sha256']}")

    try:
        consumer = subprocess.run(
            [sys.executable, str(TRIXEL_TOOL), str(REQUEST_DIR), str(RESPONSE_DIR), REQUEST_ID],
            cwd=TRIXEL_TOOL.parents[1],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        print(f"{tag}[TRIXEL_CONSUMER] timed out after 120s; loop fails closed")
        return 1
    print(f"{tag}[TRIXEL_CONSUMER] exit={consumer.returncode} {consumer.stdout.strip()}")
    if consumer.returncode != 0:
        return 1
    consumer_result = json.loads(consumer.stdout.strip())
    if consumer_result["response_sha256"] != COMPLETE_EDGE_SHA256:
        print(f"{tag}[BYTE_IDENTITY_FAILED] rebuilt response is not the pinned payload")
        return 1
    print(f"{tag}[BYTE_IDENTITY] rebuilt response equals pinned payload {COMPLETE_EDGE_SHA256}")

    result = intake_built_drop(
        RESPONSE_DIR,
        trusted_request=COMPLETE_EDGE_REQUEST,
        expected_payload_sha256=COMPLETE_EDGE_SHA256,
        expected_topology_policy=COMPLETE_EDGE_POLICY,
        receipt_path=RECEIPT_PATH,
    )
    if not result.accepted:
        print(f"{tag}[INTAKE_REJECTED] {result.errors[0]}")
        return 1
    print(f"{tag}[INTAKE_ACCEPTED] surface_id={result.receipt['surface_id']}")
    print(f"{tag}[POLICY_VERIFIED] {result.receipt['topology_policy']} before apply authorization")

    packet = complete_edge_apply_packet()
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
    print(f"{tag}[REQUEST_ID_CORRELATION] {REQUEST_ID} held end to end")
    print(f"{tag}[COLLISION_AUTHORIZED] false (denied and untested; PINCH_EDGE_NON_MANIFOLD declared)")
    print(f"{tag}[GODOT_RUNTIME_EXECUTED] false")
    print(f"{tag}[RUNTIME_QUARANTINE_CHANGED] false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
