"""Focused proofs for the apply-authorization exporter.

The exporter is the reproducible EngAIn source of the accepted
apply-authorization artifact consumed by the isolated Godot apply executor
(godotollama ea14085). These proofs lock: emission only after the unchanged
apply gate returns TRUE, deterministic bytes under the accepted SHA-256
lock, and fail-closed refusal with no partial output.
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
    BuiltSurfaceValidation,
    GateResult,
)
from tier1.engainos.gates.gate_trixel32d_surface_apply import (
    canonical_application_intent_digest,
    gate_trixel32d_surface_apply,
)
from tier1.engainos.tests.test_trixel32d_complete_edge_transport import (
    COMPLETE_EDGE_SHA256,
)
from tier1.engainos.tests.test_trixel32d_surface_apply import (
    authority_for,
    canonical_scene_truth,
)

EXPORTER_PATH = REPO_ROOT / "executors" / "trixel32d_apply_authorization_export_v1.py"

# The accepted artifact lock: the live export, the vendored godotollama
# fixture, and every deterministic rebuild must all carry these bytes.
ACCEPTED_ARTIFACT_SHA256 = (
    "5467c9c6d9e05aca564a9dbd042af62eb4893b87234c91f1d5f32b44b5fd039f"
)


def _load_exporter():
    spec = importlib.util.spec_from_file_location(
        "trixel32d_apply_authorization_export_v1", EXPORTER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def exporter():
    return _load_exporter()


def test_artifact_bytes_deterministic_under_accepted_lock(exporter) -> None:
    _, first_bytes = exporter.build_artifact()
    _, second_bytes = exporter.build_artifact()
    assert first_bytes == second_bytes
    assert hashlib.sha256(first_bytes).hexdigest() == ACCEPTED_ARTIFACT_SHA256


def test_artifact_content_is_gate_true_and_exactly_bound(exporter) -> None:
    artifact, artifact_bytes = exporter.build_artifact()
    parsed = json.loads(artifact_bytes.decode("utf-8"))
    assert parsed == artifact
    assert parsed["contract"] == "engainos.trixel32d_apply_authorization.v1"
    assert parsed["packet_type"] == "trixel32d_apply_authorization"
    assert parsed["gate_result"]["gate_name"] == "gate_trixel32d_surface_apply"
    assert parsed["gate_result"]["passed"] == "TRUE"
    assert parsed["collision_authorized"] is False
    assert parsed["godot_runtime_scope"] == "ISOLATED_APPLY_EXECUTOR_PROOF_ONLY"
    packet = parsed["apply_packet"]
    assert parsed["authorized_intent_sha256"] == canonical_application_intent_digest(
        packet
    )
    assert parsed["payload_binding"] == packet["surface_binding"]
    assert packet["surface_binding"]["built_response_sha256"] == COMPLETE_EDGE_SHA256
    collision = packet["collision"]
    assert collision["decision"] == "DENIED"
    assert collision["shape_policy"] == "NONE"
    assert collision["layer"] == 0 and collision["mask"] == 0


def test_gate_refusal_stops_emission_with_no_partial_output(
    exporter, tmp_path, monkeypatch
) -> None:
    export_dir = tmp_path / "t32ddrop_gate_false"
    monkeypatch.setattr(exporter, "EXPORT_DIR", export_dir)
    monkeypatch.setattr(
        exporter, "ARTIFACT_PATH", export_dir / "TRIXEL32D_SURFACE_APPLY_AUTHORIZATION_V1.json"
    )
    monkeypatch.setattr(
        exporter,
        "gate_trixel32d_surface_apply",
        lambda *args, **kwargs: GateResult(
            gate_name="gate_trixel32d_surface_apply",
            passed="FALSE",
            message="forced refusal for the fail-closed proof",
        ),
    )
    with pytest.raises(SystemExit) as refusal:
        exporter.main()
    assert "apply gate refused" in str(refusal.value)
    assert not export_dir.exists()


def test_gate_itself_refuses_unaccepted_validation(exporter) -> None:
    # The enforcement point is the unchanged gate, not the exporter's
    # redundant assert: a rejected byte-level validation must gate FALSE.
    packet, _ = exporter.build_artifact()
    apply_packet = packet["apply_packet"]
    rejected = BuiltSurfaceValidation(
        response_sha256=None, packet=None, errors=("forced rejection",)
    )
    outcome = gate_trixel32d_surface_apply(
        apply_packet,
        built_validation=rejected,
        authority=authority_for(apply_packet),
        scene_truth=canonical_scene_truth(),
    )
    assert outcome.is_false()


def test_occupied_slot_refuses_without_touching_bytes(
    exporter, tmp_path, monkeypatch
) -> None:
    export_dir = tmp_path / "t32ddrop_occupied"
    export_dir.mkdir(parents=True)
    artifact_path = export_dir / "TRIXEL32D_SURFACE_APPLY_AUTHORIZATION_V1.json"
    sentinel = b'{"sentinel": "occupied slot is the consume state"}'
    artifact_path.write_bytes(sentinel)
    monkeypatch.setattr(exporter, "EXPORT_DIR", export_dir)
    monkeypatch.setattr(exporter, "ARTIFACT_PATH", artifact_path)
    assert exporter.main() == 1
    assert artifact_path.read_bytes() == sentinel
