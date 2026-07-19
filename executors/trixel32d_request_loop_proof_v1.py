#!/usr/bin/env python3
"""Passive request-side transport loop proof (TRIXEL32D_REQUEST_LOOP_PROOF_V1).

Drives the complete passive chain across the real drop slots:
EngAInOS dispatch (exact vendored request bytes) -> Trixel command consumer
(separate process; no cross-repo code import) -> checksum-locked built
response drop -> committed EngAIn intake -> intent-bound apply authorization
-> receipt. Refuses occupied slots instead of overwriting them. No Godot
runtime execution, scene attachment, placement, collision allocation, world
mutation, or runtime-quarantine change.
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
from tier1.engainos.tests.test_trixel32d_built_drop_intake import (
    CONNECTED_REQUEST,
    CONNECTED_SHA256,
    REQUEST_ID,
    STITCHED_POLICY,
    stitched_apply_packet,
)
from tier1.engainos.tests.test_trixel32d_surface_apply import (
    authority_for,
    canonical_scene_truth,
)

REQUEST_DIR = ROOT / "runtime" / "trixel32d_requests"
RESPONSE_DIR = ROOT / "runtime" / "trixel32d_built_drops"
RECEIPT_PATH = ROOT / "runtime" / "trixel32d_reports" / RECEIPT_FILENAME
REQUEST_FIXTURE = ROOT / "tier1" / "engainos" / "tests" / "fixtures" / "trixel32d_request_texel_connected.json"
TRIXEL_TOOL = ROOT.parent / "trixel3.2d" / "tools" / "consume_trixel32d_request_drop.py"


def main() -> int:
    tag = "[trixel32d_request_loop_proof]"

    for occupied, label in (
        (REQUEST_DIR / REQUEST_ENVELOPE_FILENAME, "request drop slot"),
        (RESPONSE_DIR / RESPONSE_ENVELOPE_FILENAME, "response drop slot"),
        (RECEIPT_PATH, "intake receipt slot"),
    ):
        if occupied.exists():
            print(f"{tag}[SLOT_OCCUPIED] {label}: {occupied}")
            print(f"{tag}[REFUSED] clear consumed slots explicitly before a new loop run")
            return 1

    request_bytes = REQUEST_FIXTURE.read_bytes()
    dispatch = dispatch_request_drop(REQUEST_DIR, request_bytes, generated_by="engainos")
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
    if consumer_result["response_sha256"] != CONNECTED_SHA256:
        print(f"{tag}[BYTE_IDENTITY_FAILED] rebuilt response is not the pinned payload")
        return 1
    print(f"{tag}[BYTE_IDENTITY] rebuilt response equals pinned payload {CONNECTED_SHA256}")

    result = intake_built_drop(
        RESPONSE_DIR,
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
    print(f"{tag}[REQUEST_ID_CORRELATION] {REQUEST_ID} held end to end")
    print(f"{tag}[COLLISION_AUTHORIZED] false (T_JUNCTION_WALL_EDGES limitation)")
    print(f"{tag}[GODOT_RUNTIME_EXECUTED] false")
    print(f"{tag}[RUNTIME_QUARANTINE_CHANGED] false")
    print(f"{tag}[REQUEST_SHA256] {hashlib.sha256(request_bytes).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
