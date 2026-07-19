from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.bridgeroom.trixel32d_request_dispatch import (
    REQUEST_ENVELOPE_FILENAME,
    REQUEST_PAYLOAD_FILENAME,
    dispatch_request_drop,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
REQUEST_PATH = FIXTURE_DIR / "trixel32d_request_texel_connected.json"
REQUEST_BYTES = REQUEST_PATH.read_bytes()
REQUEST_SHA256 = hashlib.sha256(REQUEST_BYTES).hexdigest()
REQUEST_ID = "t32dreq_001241884d12dff0"


def test_dispatch_writes_exact_bytes_and_binding_envelope(tmp_path):
    result = dispatch_request_drop(tmp_path, REQUEST_BYTES, generated_by="engainos")
    assert result.dispatched, result.errors

    written = (tmp_path / REQUEST_PAYLOAD_FILENAME).read_bytes()
    assert written == REQUEST_BYTES

    envelope = json.loads((tmp_path / REQUEST_ENVELOPE_FILENAME).read_text(encoding="utf-8"))
    assert envelope == dict(result.envelope)
    assert envelope["payload_sha256"] == REQUEST_SHA256
    assert envelope["drop_id"] == f"t32ddrop_{REQUEST_SHA256[:16]}"
    assert envelope["request_id"] == REQUEST_ID
    assert envelope["topology_policy"] == "HEIGHT_FIELD_CONNECTED_SURFACE"


def test_invalid_request_bytes_dispatch_nothing(tmp_path):
    result = dispatch_request_drop(tmp_path, b"{not json", generated_by="engainos")
    assert not result.dispatched
    assert any("could not be parsed" in e for e in result.errors)
    assert list(tmp_path.iterdir()) == [] if tmp_path.exists() else True

    request = json.loads(REQUEST_BYTES.decode("utf-8"))
    request["gap_fill"]["mode"] = "PER_CELL_EXTRUSION"
    bad_bytes = json.dumps(request, indent=1, sort_keys=True).encode("utf-8")
    result = dispatch_request_drop(tmp_path, bad_bytes, generated_by="engainos")
    assert not result.dispatched
    assert any("request failed validation" in e for e in result.errors)
    assert not (tmp_path / REQUEST_PAYLOAD_FILENAME).exists()
    assert not (tmp_path / REQUEST_ENVELOPE_FILENAME).exists()


def test_duplicate_dispatch_rejects_without_overwriting(tmp_path):
    first = dispatch_request_drop(tmp_path, REQUEST_BYTES, generated_by="engainos")
    assert first.dispatched
    before = (tmp_path / REQUEST_PAYLOAD_FILENAME).read_bytes()

    second = dispatch_request_drop(tmp_path, REQUEST_BYTES, generated_by="engainos")
    assert not second.dispatched
    assert any("duplicate dispatch rejects" in e for e in second.errors)
    assert (tmp_path / REQUEST_PAYLOAD_FILENAME).read_bytes() == before


def test_dispatch_does_not_mutate_source_fixture(tmp_path):
    dispatch_request_drop(tmp_path, REQUEST_BYTES, generated_by="engainos")
    assert hashlib.sha256(REQUEST_PATH.read_bytes()).hexdigest() == REQUEST_SHA256
