from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from tier1.engainos.bridgeroom.trixel32d_built_drop_intake import (
    ENVELOPE_FILENAME,
    PAYLOAD_FILENAME,
    IntakeResult,
    intake_built_drop,
    write_built_drop,
    write_intake_receipt,
)
from tier1.engainos.gates.gate_trixel32d_surface_apply import gate_trixel32d_surface_apply
from tier1.engainos.tests.test_trixel32d_surface_apply import (
    authority_for,
    canonical_apply_packet,
    canonical_scene_truth,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
CONNECTED_PAYLOAD_PATH = FIXTURE_DIR / "trixel32d_surface_built_texel_connected.json"
LATTICE_PAYLOAD_PATH = FIXTURE_DIR / "trixel32d_surface_built_texel_lattice.json"
CONNECTED_PAYLOAD = CONNECTED_PAYLOAD_PATH.read_bytes()
LATTICE_PAYLOAD = LATTICE_PAYLOAD_PATH.read_bytes()
CONNECTED_SHA256 = hashlib.sha256(CONNECTED_PAYLOAD).hexdigest()
LATTICE_SHA256 = hashlib.sha256(LATTICE_PAYLOAD).hexdigest()
CONNECTED_REQUEST = json.loads(
    (FIXTURE_DIR / "trixel32d_request_texel_connected.json").read_text(encoding="utf-8")
)
LATTICE_REQUEST = json.loads(
    (FIXTURE_DIR / "trixel32d_request_texel_lattice.json").read_text(encoding="utf-8")
)

REQUEST_ID = "t32dreq_001241884d12dff0"
STITCHED_SURFACE_ID = "t32dsurface_f024725d200e470c"
LATTICE_SURFACE_ID = "t32dsurface_245be4a987cf6fd9"
STITCHED_POLICY = "HEIGHT_FIELD_CONNECTED_SURFACE"
LATTICE_POLICY = "HEIGHT_FIELD_CELL_EXTRUSION"


def write_stitched_drop(drop_dir: Path) -> dict[str, Any]:
    return write_built_drop(
        drop_dir,
        CONNECTED_PAYLOAD,
        generated_by="trixel3.2d",
        request_id=REQUEST_ID,
        surface_id=STITCHED_SURFACE_ID,
        topology_policy=STITCHED_POLICY,
    )


def write_lattice_drop(drop_dir: Path) -> dict[str, Any]:
    return write_built_drop(
        drop_dir,
        LATTICE_PAYLOAD,
        generated_by="trixel3.2d",
        request_id=REQUEST_ID,
        surface_id=LATTICE_SURFACE_ID,
        topology_policy=LATTICE_POLICY,
    )


def run_intake(drop_dir: Path, receipt: Path, **overrides: Any) -> IntakeResult:
    values: dict[str, Any] = {
        "trusted_request": CONNECTED_REQUEST,
        "expected_payload_sha256": CONNECTED_SHA256,
        "expected_topology_policy": STITCHED_POLICY,
        "receipt_path": receipt,
    }
    values.update(overrides)
    return intake_built_drop(drop_dir, **values)


def stitched_apply_packet() -> dict[str, Any]:
    packet = canonical_apply_packet()
    packet["surface_binding"] = {
        "built_contract": "trixel32d_surface_built.v1",
        "request_id": REQUEST_ID,
        "surface_id": STITCHED_SURFACE_ID,
        "built_response_sha256": CONNECTED_SHA256,
    }
    return packet


def test_exact_stitched_drop_transports_unchanged_and_accepts(tmp_path):
    drop_dir = tmp_path / "drops"
    receipt_path = tmp_path / "receipt.json"
    envelope = write_stitched_drop(drop_dir)
    assert envelope["payload_sha256"] == CONNECTED_SHA256

    transported = (drop_dir / PAYLOAD_FILENAME).read_bytes()
    assert transported == CONNECTED_PAYLOAD

    result = run_intake(drop_dir, receipt_path)
    assert result.accepted, result.errors
    assert result.validation is not None
    assert result.validation.response_sha256 == CONNECTED_SHA256
    assert result.receipt["payload_sha256"] == CONNECTED_SHA256
    assert result.receipt["request_id"] == REQUEST_ID
    assert result.receipt["surface_id"] == STITCHED_SURFACE_ID
    assert result.receipt["topology_policy"] == STITCHED_POLICY
    assert result.receipt["collision_authorized"] is False
    assert result.receipt["godot_runtime_executed"] is False
    assert result.receipt["scene_attached"] is False
    assert result.receipt["world_mutated"] is False
    assert result.receipt["runtime_quarantine_changed"] is False

    written = write_intake_receipt(receipt_path, result)
    assert written.is_file()
    assert CONNECTED_PAYLOAD_PATH.read_bytes() == CONNECTED_PAYLOAD


def test_full_chain_reaches_intent_bound_apply_authorization(tmp_path):
    drop_dir = tmp_path / "drops"
    receipt_path = tmp_path / "receipt.json"
    write_stitched_drop(drop_dir)
    result = run_intake(drop_dir, receipt_path)
    assert result.accepted, result.errors

    packet = stitched_apply_packet()
    outcome = gate_trixel32d_surface_apply(
        packet,
        built_validation=result.validation,
        authority=authority_for(packet),
        scene_truth=canonical_scene_truth(),
    )
    assert outcome.is_true(), outcome.message


def test_lattice_payload_cannot_substitute_for_stitched(tmp_path):
    # a) lattice drop against the stitched expected identity: stale before parse
    drop_dir = tmp_path / "a"
    write_lattice_drop(drop_dir)
    result = run_intake(drop_dir, tmp_path / "ra.json")
    assert not result.accepted
    assert any("stale" in e for e in result.errors)

    # b) even with the expectation forged to the lattice checksum, the
    #    authorized-topology check rejects the lattice payload
    drop_dir = tmp_path / "b"
    write_lattice_drop(drop_dir)
    result = run_intake(
        drop_dir,
        tmp_path / "rb.json",
        trusted_request=LATTICE_REQUEST,
        expected_payload_sha256=LATTICE_SHA256,
    )
    assert not result.accepted
    assert any("not the authorized" in e for e in result.errors)

    # c) apply-level: an authority intent-bound to the stitched surface does
    #    not cover an apply packet rebound to the lattice surface
    stitched_authority = authority_for(stitched_apply_packet())
    lattice_bound = stitched_apply_packet()
    lattice_bound["surface_binding"]["surface_id"] = LATTICE_SURFACE_ID
    lattice_bound["surface_binding"]["built_response_sha256"] = LATTICE_SHA256

    lattice_dir = tmp_path / "c"
    write_lattice_drop(lattice_dir)
    lattice_result = run_intake(
        lattice_dir,
        tmp_path / "rc.json",
        trusted_request=LATTICE_REQUEST,
        expected_payload_sha256=LATTICE_SHA256,
        expected_topology_policy=LATTICE_POLICY,
    )
    assert lattice_result.accepted, lattice_result.errors

    outcome = gate_trixel32d_surface_apply(
        lattice_bound,
        built_validation=lattice_result.validation,
        authority=stitched_authority,
        scene_truth=canonical_scene_truth(),
    )
    assert outcome.is_false()
    assert "exact application intent" in outcome.message


def test_stitched_payload_cannot_substitute_for_lattice(tmp_path):
    drop_dir = tmp_path / "drops"
    write_stitched_drop(drop_dir)
    result = run_intake(
        drop_dir,
        tmp_path / "receipt.json",
        expected_topology_policy=LATTICE_POLICY,
    )
    assert not result.accepted
    assert any("not the authorized" in e for e in result.errors)


def test_swapped_validation_evidence_fails_surface_binding(tmp_path):
    lattice_dir = tmp_path / "lattice"
    write_lattice_drop(lattice_dir)
    lattice_result = run_intake(
        lattice_dir,
        tmp_path / "receipt.json",
        trusted_request=LATTICE_REQUEST,
        expected_payload_sha256=LATTICE_SHA256,
        expected_topology_policy=LATTICE_POLICY,
    )
    assert lattice_result.accepted, lattice_result.errors

    packet = stitched_apply_packet()
    outcome = gate_trixel32d_surface_apply(
        packet,
        built_validation=lattice_result.validation,
        authority=authority_for(packet),
        scene_truth=canonical_scene_truth(),
    )
    assert outcome.is_false()


def test_malformed_envelope_rejects(tmp_path):
    drop_dir = tmp_path / "drops"
    receipt = tmp_path / "receipt.json"

    write_stitched_drop(drop_dir)
    (drop_dir / ENVELOPE_FILENAME).write_text("{not json", encoding="utf-8")
    result = run_intake(drop_dir, receipt)
    assert not result.accepted
    assert any("could not be parsed" in e for e in result.errors)

    envelope = write_stitched_drop(drop_dir)
    envelope["extra"] = True
    (drop_dir / ENVELOPE_FILENAME).write_text(json.dumps(envelope), encoding="utf-8")
    result = run_intake(drop_dir, receipt)
    assert any("undeclared keys" in e for e in result.errors)

    envelope = write_stitched_drop(drop_dir)
    del envelope["surface_id"]
    (drop_dir / ENVELOPE_FILENAME).write_text(json.dumps(envelope), encoding="utf-8")
    result = run_intake(drop_dir, receipt)
    assert any("missing required keys" in e for e in result.errors)

    envelope = write_stitched_drop(drop_dir)
    envelope["payload_file"] = "../evil.json"
    (drop_dir / ENVELOPE_FILENAME).write_text(json.dumps(envelope), encoding="utf-8")
    result = run_intake(drop_dir, receipt)
    assert any("payload_file must be exactly" in e for e in result.errors)

    envelope = write_stitched_drop(drop_dir)
    envelope["drop_id"] = "t32ddrop_0000000000000000"
    (drop_dir / ENVELOPE_FILENAME).write_text(json.dumps(envelope), encoding="utf-8")
    result = run_intake(drop_dir, receipt)
    assert any("drop_id must derive from the payload checksum" in e for e in result.errors)


def test_truncated_payload_rejects_before_parse(tmp_path):
    drop_dir = tmp_path / "drops"
    write_stitched_drop(drop_dir)
    (drop_dir / PAYLOAD_FILENAME).write_bytes(CONNECTED_PAYLOAD[: len(CONNECTED_PAYLOAD) // 2])
    result = run_intake(drop_dir, tmp_path / "receipt.json")
    assert not result.accepted
    assert any("do not match the declared checksum" in e for e in result.errors)


def test_envelope_misdeclaring_identity_rejects(tmp_path):
    drop_dir = tmp_path / "drops"
    envelope = write_stitched_drop(drop_dir)
    envelope["surface_id"] = LATTICE_SURFACE_ID
    (drop_dir / ENVELOPE_FILENAME).write_text(
        json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8"
    )
    result = run_intake(drop_dir, tmp_path / "receipt.json")
    assert not result.accepted
    assert any("misdeclaring envelope rejects" in e for e in result.errors)


def test_duplicate_consume_rejects(tmp_path):
    drop_dir = tmp_path / "drops"
    receipt_path = tmp_path / "receipt.json"
    write_stitched_drop(drop_dir)
    first = run_intake(drop_dir, receipt_path)
    assert first.accepted
    write_intake_receipt(receipt_path, first)

    second = run_intake(drop_dir, receipt_path)
    assert not second.accepted
    assert any("duplicate consume rejects" in e for e in second.errors)

    with pytest.raises(FileExistsError):
        write_intake_receipt(receipt_path, first)


def test_collision_remains_unauthorized_for_stitched_payload(tmp_path):
    drop_dir = tmp_path / "drops"
    write_stitched_drop(drop_dir)
    result = run_intake(drop_dir, tmp_path / "receipt.json")
    assert result.accepted
    assert result.receipt["collision_authorized"] is False

    packet = stitched_apply_packet()
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


def test_intake_mutates_no_source_bytes(tmp_path):
    drop_dir = tmp_path / "drops"
    write_stitched_drop(drop_dir)
    before_drop = (drop_dir / PAYLOAD_FILENAME).read_bytes()
    run_intake(drop_dir, tmp_path / "receipt.json")
    assert (drop_dir / PAYLOAD_FILENAME).read_bytes() == before_drop
    assert hashlib.sha256(CONNECTED_PAYLOAD_PATH.read_bytes()).hexdigest() == CONNECTED_SHA256
    assert hashlib.sha256(LATTICE_PAYLOAD_PATH.read_bytes()).hexdigest() == LATTICE_SHA256
