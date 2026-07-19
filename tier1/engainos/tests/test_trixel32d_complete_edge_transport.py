from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.bridgeroom.trixel32d_built_drop_intake import (
    intake_built_drop,
    write_built_drop,
)
from tier1.engainos.bridgeroom.trixel32d_request_dispatch import (
    REQUEST_PAYLOAD_FILENAME,
    dispatch_request_drop,
)
from tier1.engainos.gates.gate_trixel32d_surface_apply import (
    canonical_application_intent_digest,
    gate_trixel32d_surface_apply,
)
from tier1.engainos.tests.test_trixel32d_built_drop_intake import (
    CONNECTED_PAYLOAD,
    CONNECTED_SHA256,
    LATTICE_PAYLOAD,
    LATTICE_SHA256,
    REQUEST_ID,
    STITCHED_SURFACE_ID,
    LATTICE_SURFACE_ID,
    STITCHED_POLICY,
    LATTICE_POLICY,
    stitched_apply_packet,
)
from tier1.engainos.tests.test_trixel32d_surface_apply import (
    authority_for,
    canonical_authority,
    canonical_scene_truth,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
COMPLETE_EDGE_PAYLOAD_PATH = FIXTURE_DIR / "trixel32d_surface_built_texel_complete_edge.json"
COMPLETE_EDGE_PAYLOAD = COMPLETE_EDGE_PAYLOAD_PATH.read_bytes()
COMPLETE_EDGE_SHA256 = hashlib.sha256(COMPLETE_EDGE_PAYLOAD).hexdigest()
COMPLETE_EDGE_REQUEST_PATH = FIXTURE_DIR / "trixel32d_request_texel_complete_edge.json"
COMPLETE_EDGE_REQUEST_BYTES = COMPLETE_EDGE_REQUEST_PATH.read_bytes()
COMPLETE_EDGE_REQUEST = json.loads(COMPLETE_EDGE_REQUEST_BYTES.decode("utf-8"))

COMPLETE_EDGE_POLICY = "HEIGHT_FIELD_COMPLETE_EDGE_CONNECTED_SURFACE"
COMPLETE_EDGE_SURFACE_ID = "t32dsurface_cd7eee9d7877c948"
PINNED_COMPLETE_EDGE_SHA256 = "49396807a2d119328608b44203c0a8aae20cfe5ac0028e880676ac538bb7745b"

PAYLOADS = {
    "lattice": (LATTICE_PAYLOAD, LATTICE_SHA256, LATTICE_SURFACE_ID, LATTICE_POLICY),
    "stitched": (CONNECTED_PAYLOAD, CONNECTED_SHA256, STITCHED_SURFACE_ID, STITCHED_POLICY),
    "complete_edge": (
        COMPLETE_EDGE_PAYLOAD, COMPLETE_EDGE_SHA256,
        COMPLETE_EDGE_SURFACE_ID, COMPLETE_EDGE_POLICY,
    ),
}


def test_pinned_identity_holds():
    assert COMPLETE_EDGE_SHA256 == PINNED_COMPLETE_EDGE_SHA256
    assert COMPLETE_EDGE_REQUEST["identity"]["request_id"] == REQUEST_ID
    assert COMPLETE_EDGE_REQUEST["construction"]["topology_policy"] == COMPLETE_EDGE_POLICY


def write_drop_for(kind: str, drop_dir: Path) -> None:
    payload, sha, surface_id, policy = PAYLOADS[kind]
    write_built_drop(
        drop_dir,
        payload,
        generated_by="trixel3.2d",
        request_id=REQUEST_ID,
        surface_id=surface_id,
        topology_policy=policy,
    )


def complete_edge_apply_packet() -> dict[str, Any]:
    packet = stitched_apply_packet()
    packet["surface_binding"]["surface_id"] = COMPLETE_EDGE_SURFACE_ID
    packet["surface_binding"]["built_response_sha256"] = COMPLETE_EDGE_SHA256
    return packet


def test_complete_edge_dispatch_intake_and_apply(tmp_path):
    dispatch = dispatch_request_drop(
        tmp_path / "req", COMPLETE_EDGE_REQUEST_BYTES, generated_by="engainos"
    )
    assert dispatch.dispatched, dispatch.errors
    assert (tmp_path / "req" / REQUEST_PAYLOAD_FILENAME).read_bytes() == COMPLETE_EDGE_REQUEST_BYTES
    assert dispatch.envelope["topology_policy"] == COMPLETE_EDGE_POLICY

    drop_dir = tmp_path / "resp"
    write_drop_for("complete_edge", drop_dir)
    result = intake_built_drop(
        drop_dir,
        trusted_request=COMPLETE_EDGE_REQUEST,
        expected_payload_sha256=COMPLETE_EDGE_SHA256,
        expected_topology_policy=COMPLETE_EDGE_POLICY,
        receipt_path=tmp_path / "receipt.json",
    )
    assert result.accepted, result.errors
    assert result.receipt["surface_id"] == COMPLETE_EDGE_SURFACE_ID
    assert result.receipt["topology_policy"] == COMPLETE_EDGE_POLICY
    assert result.receipt["collision_authorized"] is False

    packet = complete_edge_apply_packet()
    outcome = gate_trixel32d_surface_apply(
        packet,
        built_validation=result.validation,
        authority=authority_for(packet),
        scene_truth=canonical_scene_truth(),
    )
    assert outcome.is_true(), outcome.message


def test_three_way_substitution_rejects_at_checksum_layer(tmp_path):
    for actual in PAYLOADS:
        for expected in PAYLOADS:
            if actual == expected:
                continue
            drop_dir = tmp_path / f"{actual}_as_{expected}"
            write_drop_for(actual, drop_dir)
            _, expected_sha, _, expected_policy = PAYLOADS[expected]
            result = intake_built_drop(
                drop_dir,
                trusted_request=COMPLETE_EDGE_REQUEST,
                expected_payload_sha256=expected_sha,
                expected_topology_policy=expected_policy,
                receipt_path=drop_dir / "receipt.json",
            )
            assert not result.accepted, (actual, expected)
            assert any("stale" in e for e in result.errors), (actual, expected, result.errors)


def test_three_way_substitution_rejects_at_policy_layer(tmp_path):
    requests = {
        "lattice": json.loads(
            (FIXTURE_DIR / "trixel32d_request_texel_lattice.json").read_text(encoding="utf-8")
        ),
        "stitched": json.loads(
            (FIXTURE_DIR / "trixel32d_request_texel_connected.json").read_text(encoding="utf-8")
        ),
        "complete_edge": COMPLETE_EDGE_REQUEST,
    }
    for actual in PAYLOADS:
        for expected in PAYLOADS:
            if actual == expected:
                continue
            # Forge the checksum expectation to the actual payload: the
            # authorized-topology check must still reject the substitution.
            drop_dir = tmp_path / f"{actual}_forged_as_{expected}"
            write_drop_for(actual, drop_dir)
            actual_payload, actual_sha, _, _ = PAYLOADS[actual]
            _, _, _, expected_policy = PAYLOADS[expected]
            result = intake_built_drop(
                drop_dir,
                trusted_request=requests[actual],
                expected_payload_sha256=actual_sha,
                expected_topology_policy=expected_policy,
                receipt_path=drop_dir / "receipt.json",
            )
            assert not result.accepted, (actual, expected)
            assert any("not the authorized" in e for e in result.errors), (actual, expected)


def test_three_way_substitution_rejects_at_intent_digest_layer(tmp_path):
    complete_edge_authority = authority_for(complete_edge_apply_packet())
    drop_dir = tmp_path / "stitched"
    write_drop_for("stitched", drop_dir)
    stitched_request = json.loads(
        (FIXTURE_DIR / "trixel32d_request_texel_connected.json").read_text(encoding="utf-8")
    )
    stitched_result = intake_built_drop(
        drop_dir,
        trusted_request=stitched_request,
        expected_payload_sha256=CONNECTED_SHA256,
        expected_topology_policy=STITCHED_POLICY,
        receipt_path=tmp_path / "receipt.json",
    )
    assert stitched_result.accepted, stitched_result.errors

    rebound = stitched_apply_packet()
    outcome = gate_trixel32d_surface_apply(
        rebound,
        built_validation=stitched_result.validation,
        authority=complete_edge_authority,
        scene_truth=canonical_scene_truth(),
    )
    assert outcome.is_false()
    assert "exact application intent" in outcome.message

    # The digests themselves are pairwise distinct across all three bindings.
    digests = set()
    for kind, (_, sha, surface_id, _) in PAYLOADS.items():
        packet = stitched_apply_packet()
        packet["surface_binding"]["surface_id"] = surface_id
        packet["surface_binding"]["built_response_sha256"] = sha
        digests.add(canonical_application_intent_digest(packet))
    assert len(digests) == 3


def test_collision_remains_denied_for_complete_edge(tmp_path):
    drop_dir = tmp_path / "resp"
    write_drop_for("complete_edge", drop_dir)
    result = intake_built_drop(
        drop_dir,
        trusted_request=COMPLETE_EDGE_REQUEST,
        expected_payload_sha256=COMPLETE_EDGE_SHA256,
        expected_topology_policy=COMPLETE_EDGE_POLICY,
        receipt_path=tmp_path / "receipt.json",
    )
    assert result.accepted

    packet = complete_edge_apply_packet()
    packet["classification"] = "STATIC_SPATIAL"
    packet["collision"] = {
        "decision": "GRANTED",
        "authorized_by_decision_id": packet["authorization"]["decision_id"],
        "shape_policy": "CANONICAL_MESH_EXACT",
        "layer": 1,
        "mask": 0,
    }
    outcome = gate_trixel32d_surface_apply(
        packet,
        built_validation=result.validation,
        authority=authority_for(packet),
        scene_truth=canonical_scene_truth(),
    )
    assert outcome.is_false()
    assert "collision" in outcome.message.lower()


def test_source_fixtures_unmodified():
    assert hashlib.sha256(COMPLETE_EDGE_PAYLOAD_PATH.read_bytes()).hexdigest() == PINNED_COMPLETE_EDGE_SHA256
    trixel_owned = (
        REPO_ROOT.parent / "trixel3.2d" / "fixtures" / "texel"
        / "texel_complete_edge_surface_built_response.json"
    )
    assert trixel_owned.read_bytes() == COMPLETE_EDGE_PAYLOAD
