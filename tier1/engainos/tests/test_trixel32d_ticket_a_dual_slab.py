"""Roadmap Ticket A: dual-slab application evidence proofs.

Covers the parametrized apply-authorization exporter's stone (second-tile)
path and a complete ordered substitution matrix across the four payload
identities that cross the Trixel -> EngAIn boundary (payload_sha256,
request_id, surface_id, topology_policy), each proven at the layer where
that identity is actually checked: the built-response validation boundary
(payload_sha256, request_id, topology_policy) or the apply-authorization
gate's built-binding cross-check (payload_sha256, request_id, surface_id).
The Godot isolated executor supplies the third layer (its own toxic test,
committed in godotollama) for the substitution attacks that can reach a
scene-tree attachment. Twelve ordered cases total.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.gates.gate_trixel32d_handshake import (
    validate_trixel32d_surface_built_bytes,
)
from tier1.engainos.gates.gate_trixel32d_surface_apply import (
    gate_trixel32d_surface_apply,
)

FIXTURES = REPO_ROOT / "tier1" / "engainos" / "tests" / "fixtures"

GRASS_PAYLOAD = (FIXTURES / "trixel32d_surface_built_texel_complete_edge.json").read_bytes()
GRASS_REQUEST = json.loads(
    (FIXTURES / "trixel32d_request_texel_complete_edge.json").read_text(encoding="utf-8")
)
GRASS_SHA256 = hashlib.sha256(GRASS_PAYLOAD).hexdigest()

STONE_PAYLOAD = (FIXTURES / "trixel32d_surface_built_texel_stone_complete_edge.json").read_bytes()
STONE_REQUEST = json.loads(
    (FIXTURES / "trixel32d_request_texel_stone_complete_edge.json").read_text(encoding="utf-8")
)
STONE_SHA256 = hashlib.sha256(STONE_PAYLOAD).hexdigest()

LATTICE_PAYLOAD = (FIXTURES / "trixel32d_surface_built_3x2_first_proof.json").read_bytes()
LATTICE_REQUEST = json.loads(
    (FIXTURES / "trixel32d_request_3x2_first_proof.json").read_text(encoding="utf-8")
)
LATTICE_SHA256 = hashlib.sha256(LATTICE_PAYLOAD).hexdigest()

EXPORTER_PATH = REPO_ROOT / "executors" / "trixel32d_apply_authorization_export_v1.py"


def _load_exporter():
    spec = importlib.util.spec_from_file_location(
        "trixel32d_apply_authorization_export_v1_dual", EXPORTER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EXPORTER = _load_exporter()
HISTORICAL_GRASS_SHA256 = "5467c9c6d9e05aca564a9dbd042af62eb4893b87234c91f1d5f32b44b5fd039f"
HISTORICAL_GRASS_PATH = (
    REPO_ROOT
    / "runtime"
    / "trixel32d_apply_authorizations"
    / "t32ddrop_49396807a2d11932"
    / "TRIXEL32D_SURFACE_APPLY_AUTHORIZATION_V1.json"
)


# ---------------------------------------------------------------------
# Ticket A common-exporter authorization path
# ---------------------------------------------------------------------


def _grass_kwargs() -> dict:
    return dict(
        payload_path=EXPORTER.GRASS_PAYLOAD_PATH,
        request_path=EXPORTER.GRASS_REQUEST_PATH,
        expected_payload_sha256=EXPORTER.GRASS_EXPECTED_SHA256,
        apply_id=EXPORTER.GRASS_APPLY_ID,
        request_id=EXPORTER.GRASS_REQUEST_ID,
        surface_id=EXPORTER.GRASS_SURFACE_ID,
        application_slot_id=EXPORTER.GRASS_SLOT_ID,
        origin=EXPORTER.GRASS_ORIGIN,
        scene_truth_path=EXPORTER.SCENE_TRUTH_PATH,
        authority_decision_id=EXPORTER.GRASS_TICKET_A_DECISION_ID,
    )


def _stone_kwargs() -> dict:
    return dict(
        payload_path=EXPORTER.STONE_PAYLOAD_PATH,
        request_path=EXPORTER.STONE_REQUEST_PATH,
        expected_payload_sha256=EXPORTER.STONE_EXPECTED_SHA256,
        apply_id=EXPORTER.STONE_APPLY_ID,
        request_id=EXPORTER.STONE_REQUEST_ID,
        surface_id=EXPORTER.STONE_SURFACE_ID,
        application_slot_id=EXPORTER.STONE_SLOT_ID,
        origin=EXPORTER.STONE_ORIGIN,
        scene_truth_path=EXPORTER.SCENE_TRUTH_PATH,
        authority_decision_id=EXPORTER.STONE_TICKET_A_DECISION_ID,
    )


def test_ticket_a_exports_are_deterministic() -> None:
    for tile in ("grass", "stone"):
        artifact1, bytes1 = EXPORTER.build_ticket_a_artifact(tile)
        artifact2, bytes2 = EXPORTER.build_ticket_a_artifact(tile)
        assert bytes1 == bytes2
        assert artifact1 == artifact2
        assert artifact1["gate_result"]["passed"] == "TRUE"
        assert artifact1["collision_authorized"] is False


def test_ticket_a_both_authorizations_bind_same_authority_owned_scene_truth() -> None:
    scene_truth_bytes = EXPORTER.SCENE_TRUTH_PATH.read_bytes()
    expected_binding = {
        "contract": "engainos.trixel32d_scene_truth.v1",
        "repository_path": "tier1/engainos/authority/TRIXEL32D_SCENE_TRUTH_V1.json",
        "sha256": hashlib.sha256(scene_truth_bytes).hexdigest(),
    }
    grass, _ = EXPORTER.build_ticket_a_artifact("grass")
    stone, _ = EXPORTER.build_ticket_a_artifact("stone")
    assert grass["scene_truth_binding"] == expected_binding
    assert stone["scene_truth_binding"] == expected_binding
    assert grass["scene_truth"] == stone["scene_truth"]
    assert len(grass["scene_truth"]["declared_targets"]) == 4


def test_ticket_a_hashes_and_parses_the_same_scene_truth_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text
    authority_path = EXPORTER.SCENE_TRUTH_PATH.resolve()
    reads = 0

    def counted_read_bytes(path: Path) -> bytes:
        nonlocal reads
        if path.resolve() == authority_path:
            reads += 1
        return original_read_bytes(path)

    def counted_read_text(
        path: Path,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> str:
        nonlocal reads
        if path.resolve() == authority_path:
            reads += 1
        return original_read_text(path, encoding=encoding, errors=errors, newline=newline)

    monkeypatch.setattr(Path, "read_bytes", counted_read_bytes)
    monkeypatch.setattr(Path, "read_text", counted_read_text)
    EXPORTER.build_ticket_a_artifact("grass")
    assert reads == 1


def test_ticket_a_uses_preissued_authority_evidence_not_self_issuance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_self_issuance(_packet: dict) -> object:
        raise AssertionError("Ticket A must not derive trusted authority from its own packet")

    monkeypatch.setattr(EXPORTER, "_authority_for", forbidden_self_issuance)
    grass, _ = EXPORTER.build_ticket_a_artifact("grass")
    stone, _ = EXPORTER.build_ticket_a_artifact("stone")
    decisions = json.loads(EXPORTER.AUTHORITY_DECISIONS_PATH.read_text(encoding="utf-8"))
    by_id = {decision["decision_id"]: decision for decision in decisions["decisions"]}
    grass_id = grass["authority"]["decision_id"]
    stone_id = stone["authority"]["decision_id"]
    assert grass_id != stone_id
    assert grass_id != EXPORTER.DECISION_ID
    assert stone_id != EXPORTER.DECISION_ID
    assert grass["authorized_intent_sha256"] == by_id[grass_id]["authorized_intent_sha256"]
    assert stone["authorized_intent_sha256"] == by_id[stone_id]["authorized_intent_sha256"]
    assert grass["authority_decision_binding"] == stone["authority_decision_binding"]


def test_historical_rebuild_cannot_authorize_caller_selected_intent() -> None:
    with pytest.raises(SystemExit, match="historical rebuild path"):
        EXPORTER.build_artifact(origin=[3.0, 0.5, -1.0])


def test_preissued_decision_cannot_authorize_a_different_tile() -> None:
    with pytest.raises(SystemExit, match="does not cover the exact application intent"):
        EXPORTER.build_artifact(
            **{
                **_stone_kwargs(),
                "authority_decision_id": EXPORTER.GRASS_TICKET_A_DECISION_ID,
            }
        )


def test_ticket_a_scene_truth_source_cannot_be_substituted(tmp_path: Path) -> None:
    alternate = tmp_path / "TRIXEL32D_SCENE_TRUTH_V1.json"
    alternate.write_bytes(EXPORTER.SCENE_TRUTH_PATH.read_bytes())
    with pytest.raises(SystemExit, match="authority-owned scene truth"):
        EXPORTER.build_artifact(**{**_grass_kwargs(), "scene_truth_path": alternate})


def test_frozen_historical_grass_authorization_unchanged_and_not_ticket_a() -> None:
    historical_bytes = HISTORICAL_GRASS_PATH.read_bytes()
    _, rebuilt_historical_bytes = EXPORTER.build_artifact()
    _, fresh_grass_bytes = EXPORTER.build_ticket_a_artifact("grass")
    assert hashlib.sha256(historical_bytes).hexdigest() == HISTORICAL_GRASS_SHA256
    assert rebuilt_historical_bytes == historical_bytes
    assert fresh_grass_bytes != historical_bytes
    assert hashlib.sha256(fresh_grass_bytes).hexdigest() != HISTORICAL_GRASS_SHA256


def test_distinct_slots_and_apply_ids_for_both_surfaces() -> None:
    grass_artifact, _ = EXPORTER.build_ticket_a_artifact("grass")
    stone_artifact, _ = EXPORTER.build_ticket_a_artifact("stone")
    grass_target = grass_artifact["apply_packet"]["target"]["application_slot_id"]
    stone_target = stone_artifact["apply_packet"]["target"]["application_slot_id"]
    assert grass_target != stone_target
    assert grass_artifact["apply_packet"]["apply_id"] != stone_artifact["apply_packet"]["apply_id"]
    assert grass_artifact["apply_packet"]["surface_binding"]["surface_id"] != (
        stone_artifact["apply_packet"]["surface_binding"]["surface_id"]
    )


# ---------------------------------------------------------------------
# Layer 1: built-response validation boundary
# ---------------------------------------------------------------------


def test_l1_01_stone_bytes_against_grass_checksum_rejected() -> None:
    result = validate_trixel32d_surface_built_bytes(
        STONE_PAYLOAD, GRASS_REQUEST, expected_response_sha256=GRASS_SHA256
    )
    assert not result.accepted
    assert "checksum" in result.errors[0]


def test_l1_02_grass_bytes_against_stone_checksum_rejected() -> None:
    result = validate_trixel32d_surface_built_bytes(
        GRASS_PAYLOAD, STONE_REQUEST, expected_response_sha256=STONE_SHA256
    )
    assert not result.accepted
    assert "checksum" in result.errors[0]


def test_l1_03_stone_bytes_against_grass_request_id_rejected() -> None:
    result = validate_trixel32d_surface_built_bytes(
        STONE_PAYLOAD, GRASS_REQUEST, expected_response_sha256=STONE_SHA256
    )
    assert not result.accepted
    assert any("request_id" in e for e in result.errors)


def test_l1_04_grass_bytes_against_stone_request_id_rejected() -> None:
    result = validate_trixel32d_surface_built_bytes(
        GRASS_PAYLOAD, STONE_REQUEST, expected_response_sha256=GRASS_SHA256
    )
    assert not result.accepted
    assert any("request_id" in e for e in result.errors)


def test_l1_05_lattice_bytes_against_stone_topology_policy_rejected() -> None:
    # Stone and grass share the same topology_policy value, so a lattice
    # payload (a genuinely different declared policy) is the meaningful
    # substitution source for this identity.
    result = validate_trixel32d_surface_built_bytes(
        LATTICE_PAYLOAD, STONE_REQUEST, expected_response_sha256=LATTICE_SHA256
    )
    assert not result.accepted
    assert any("request_id" in e or "topology_policy" in e for e in result.errors)


def test_l1_06_lattice_bytes_against_grass_topology_policy_rejected() -> None:
    result = validate_trixel32d_surface_built_bytes(
        LATTICE_PAYLOAD, GRASS_REQUEST, expected_response_sha256=LATTICE_SHA256
    )
    assert not result.accepted
    assert any("request_id" in e or "topology_policy" in e for e in result.errors)


# ---------------------------------------------------------------------
# Layer 2: apply-authorization gate's built-binding cross-check
# ---------------------------------------------------------------------


def _accepted_validation(payload: bytes, request: dict, sha256: str):
    result = validate_trixel32d_surface_built_bytes(
        payload, request, expected_response_sha256=sha256
    )
    assert result.accepted, result.errors
    return result


GRASS_VALIDATION = _accepted_validation(GRASS_PAYLOAD, GRASS_REQUEST, GRASS_SHA256)
STONE_VALIDATION = _accepted_validation(STONE_PAYLOAD, STONE_REQUEST, STONE_SHA256)


def _packet_for(kwargs: dict) -> dict:
    packet, _ = EXPORTER.build_artifact(**kwargs)
    return packet["apply_packet"]


def _tampered_packet(base_kwargs: dict, mutate) -> dict:
    packet = _packet_for(base_kwargs)
    mutate(packet)
    return packet


def test_l2_07_stone_packet_with_grass_surface_id_rejected() -> None:
    packet = _tampered_packet(
        _stone_kwargs(),
        lambda p: p["surface_binding"].__setitem__("surface_id", "t32dsurface_cd7eee9d7877c948"),
    )
    outcome = gate_trixel32d_surface_apply(
        packet,
        built_validation=STONE_VALIDATION,
        authority=EXPORTER._authority_for(packet),
        scene_truth=EXPORTER._read_scene_truth(EXPORTER.SCENE_TRUTH_PATH),
    )
    assert outcome.is_false()


def test_l2_08_grass_packet_with_stone_surface_id_rejected() -> None:
    packet = _tampered_packet(
        _grass_kwargs(),
        lambda p: p["surface_binding"].__setitem__("surface_id", "t32dsurface_e33b7a00b15a4b68"),
    )
    outcome = gate_trixel32d_surface_apply(
        packet,
        built_validation=GRASS_VALIDATION,
        authority=EXPORTER._authority_for(packet),
        scene_truth=EXPORTER._read_scene_truth(EXPORTER.SCENE_TRUTH_PATH),
    )
    assert outcome.is_false()


def test_l2_09_stone_packet_with_grass_checksum_rejected() -> None:
    packet = _tampered_packet(
        _stone_kwargs(),
        lambda p: p["surface_binding"].__setitem__("built_response_sha256", GRASS_SHA256),
    )
    outcome = gate_trixel32d_surface_apply(
        packet,
        built_validation=STONE_VALIDATION,
        authority=EXPORTER._authority_for(packet),
        scene_truth=EXPORTER._read_scene_truth(EXPORTER.SCENE_TRUTH_PATH),
    )
    assert outcome.is_false()


def test_l2_10_grass_packet_with_stone_checksum_rejected() -> None:
    packet = _tampered_packet(
        _grass_kwargs(),
        lambda p: p["surface_binding"].__setitem__("built_response_sha256", STONE_SHA256),
    )
    outcome = gate_trixel32d_surface_apply(
        packet,
        built_validation=GRASS_VALIDATION,
        authority=EXPORTER._authority_for(packet),
        scene_truth=EXPORTER._read_scene_truth(EXPORTER.SCENE_TRUTH_PATH),
    )
    assert outcome.is_false()


def test_l2_11_stone_packet_with_grass_request_id_rejected() -> None:
    packet = _tampered_packet(
        _stone_kwargs(),
        lambda p: p["surface_binding"].__setitem__("request_id", "t32dreq_001241884d12dff0"),
    )
    outcome = gate_trixel32d_surface_apply(
        packet,
        built_validation=STONE_VALIDATION,
        authority=EXPORTER._authority_for(packet),
        scene_truth=EXPORTER._read_scene_truth(EXPORTER.SCENE_TRUTH_PATH),
    )
    assert outcome.is_false()


def test_l2_12_grass_packet_with_stone_request_id_rejected() -> None:
    packet = _tampered_packet(
        _grass_kwargs(),
        lambda p: p["surface_binding"].__setitem__("request_id", "t32dreq_47840250a37b492f"),
    )
    outcome = gate_trixel32d_surface_apply(
        packet,
        built_validation=GRASS_VALIDATION,
        authority=EXPORTER._authority_for(packet),
        scene_truth=EXPORTER._read_scene_truth(EXPORTER.SCENE_TRUTH_PATH),
    )
    assert outcome.is_false()
