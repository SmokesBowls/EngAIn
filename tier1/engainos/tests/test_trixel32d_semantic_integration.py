"""Real-project integration: ~/Downloads/godotnew/semantic against isolated EngAIn services.

Runs in this process, on OS-chosen loopback ports, with only disposable data
under tmp_path (ledger, drops, receipts, credentials, scene truth, policy, and
Godot's user:// via XDG_DATA_HOME):

  8080 stand-in = the *real* RuntimeHTTPHandler + EngAInRuntime with the real
                  signed presentation-observation intake, composed from a
                  disposable policy;
  8765 stand-in = the *real* SceneRequestHandler with a LiveRouteAuthority from
                  the real compose_from_environment(), whose observation source
                  is policy-derived and reads 8080's /snapshot/peek;
  control       = /test/declare (scene truth for the current runtime scene),
                  /test/build (signed build as the disposable builder client),
                  /test/restart_8765, /test/restart_8080 (in-place restarts:
                  new runtime session / instance, rotated credentials).

Then headless Godot runs res://tests/test_trixel32d_live_presentation.tscn in
the real project. Production ports, policy and runtime/ are never touched.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from pathlib import Path

import pytest

import tier1.engainos.bridgeroom.trixel32d_live_route as route
from tier1.engainos.authority.local_signed_transport import signed_headers
from tier1.engainos.bridgeroom import scene_server
from tier1.engainos.tests.test_trixel32d_request_assembler import (
    CONSTRUCTION_POLICY,
    METRIC_GRANT,
    PROVENANCE,
    build_fixture_grid_facts,
)
from tier2.godotsim import presentation_observation as po
from tier2.godotsim import sim_runtime
from tier2.godotsim.http_handlers import RuntimeHTTPHandler
from tier2.godotsim.runtime_core import EngAInRuntime

GODOT = shutil.which(os.environ.get("GODOT_BIN", "godot"))
SEMANTIC = Path(os.environ.get("ENGAIN_SEMANTIC_PROJECT", str(Path.home() / "Downloads/godotnew/semantic")))
GODOTOLLAMA = Path(os.environ.get("GODOTOLLAMA_ROOT", "/mnt/data-drive/godotollama"))
TEST_SCENE = "res://tests/test_trixel32d_live_presentation.tscn"
VENDORED = [
    "trixel_proof/trixel32d_apply_executor/godot/trixel32d_apply_executor.gd",
    "trixel_proof/trixel32d_apply_executor/godot/trixel32d_live_apply_executor.gd",
    "trixel_proof/trixel32d_passive/godot/trixel32d_surface_consumer.gd",
]

requires_semantic = pytest.mark.skipif(
    GODOT is None or not (SEMANTIC / "project.godot").is_file()
    or not (SEMANTIC / TEST_SCENE.removeprefix("res://")).is_file(),
    reason="Godot binary or godotnew/semantic integration test not available",
)

BUILDER, PRESENTER = "it-semantic-builder", "it-semantic-presenter"
SLOTS = [f"slot-a{i}" for i in range(1, 9)]
PARENT = ("RUNTIME_CONTAINER", "container-terrain-live")


@pytest.mark.skipif(not all((SEMANTIC / p).is_file() and (GODOTOLLAMA / p).is_file() for p in VENDORED),
                    reason="vendored executor copies or their godotollama originals not available")
def test_vendored_executor_copies_match_their_source():
    for rel in VENDORED:
        assert hashlib.sha256((SEMANTIC / rel).read_bytes()).hexdigest() == \
            hashlib.sha256((GODOTOLLAMA / rel).read_bytes()).hexdigest(), rel


class Services:
    def __init__(self, tmp: Path, monkeypatch):
        self.tmp = tmp
        self.runtime_root = tmp / "runtime"
        self.truth = tmp / "scene_truth.json"
        self.transport = tmp / "transport"
        self.ledger = self.runtime_root / "ledger.jsonl"
        self.policy = tmp / "policy.json"
        self.policy.write_text(json.dumps({"contract": "engainos.local_client_policy.v1", "clients": {
            BUILDER: {"actor_id": "disposable-it-builder", "actor_authority_tier": 2, "routes": ["build"]},
            PRESENTER: {"routes": ["consume", "observe"]},
        }}))
        monkeypatch.setattr(route, "RUNTIME_DIR", self.runtime_root)
        monkeypatch.setattr(route, "SCENE_TRUTH_PATH", self.truth)
        monkeypatch.setenv(route.FLAG_ENV, "1")  # this test process only
        self.lock = threading.Lock()

        self._start_runtime()
        self.runtime_server = ThreadingHTTPServer(("127.0.0.1", 0), RuntimeHTTPHandler)
        self.url_8080 = _serve(self.runtime_server)
        monkeypatch.setenv(route.RUNTIME_URL_ENV, self.url_8080)

        self.authority = None
        self._start_authority()
        self.authority_server = ThreadingHTTPServer(("127.0.0.1", 0), scene_server.SceneRequestHandler)
        self.url_8765 = _serve(self.authority_server)
        self.control_server = ThreadingHTTPServer(("127.0.0.1", 0), _control_handler(self))
        self.url_control = _serve(self.control_server)

    def _start_runtime(self):
        self.runtime = EngAInRuntime()
        RuntimeHTTPHandler.runtime = self.runtime
        sim_runtime._install_live_edit_shims(RuntimeHTTPHandler, self.runtime)
        intake, why = po.compose_from_environment(policy_path=self.policy, transport_dir=self.transport)
        assert intake is not None, why
        RuntimeHTTPHandler.presentation_intake = intake

    def _start_authority(self):
        if self.authority is not None:
            self.authority.close()
        self.authority, why = route.compose_from_environment(
            ledger_path=self.ledger, policy_path=self.policy, transport_dir=self.transport)
        assert self.authority is not None, why
        scene_server.SceneRequestHandler.trixel32d_authority = self.authority

    def declare(self):
        scene_id = self.runtime.snapshot["scene_activation"]["scene_id"]
        self.truth.write_text(json.dumps({"scene_id": scene_id,
                                          "declared_targets": [[*PARENT, s] for s in SLOTS], "slot_occupancy": {}}))
        return {"scene_id": scene_id}

    def build(self, slot_id, topology_artifact_id):
        secret = bytes.fromhex((self.transport / route.SERVER_NAME / f"{BUILDER}.key").read_text())
        body = json.dumps({
            "placement": {"mode": "scene_bound", "parent_kind": PARENT[0], "parent_id": PARENT[1],
                          "application_slot_id": slot_id, "origin": [0.0, 0.0, 0.0],
                          "basis_columns": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                          "visibility": "VISIBLE"},
            "collision": {"mode": "denied"},
            "surface": {"grid_facts": build_fixture_grid_facts(), "metric_grant": METRIC_GRANT,
                        "provenance": dict(PROVENANCE, topology_artifact_id=topology_artifact_id),
                        "construction_policy": CONSTRUCTION_POLICY},
        }).encode()
        req = urllib.request.Request(self.url_8765 + route.ROUTE_PATH, data=body, method="POST", headers={
            "Content-Type": "application/json", **signed_headers(BUILDER, secret, "POST", route.ROUTE_PATH, body)})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                code, result = resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as err:
            code, result = err.code, json.loads(err.read() or b"{}")
        out = {"code": code, "body": result}
        if code == 200:
            out.update(result["ledger_entry"])
            out["authorization_path"] = str(self.tmp / result["authorization_file"])
            out["payload_path"] = str(self.tmp / result["built_drop_dir"] / route.PAYLOAD_FILENAME)
        return out

    def restart_8765(self):
        self._start_authority()
        return {"runtime_session_id": self.authority.runtime_session_id}

    def restart_8080(self):
        self._start_runtime()
        return {"runtime_instance_id": self.runtime.runtime_instance_id}

    def close(self):
        for server in (self.control_server, self.authority_server, self.runtime_server):
            server.shutdown()
            server.server_close()
        self.authority.close()
        RuntimeHTTPHandler.presentation_intake = None
        scene_server.SceneRequestHandler.trixel32d_authority = None


def _serve(server):
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}"


def _control_handler(services: Services):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            with services.lock:
                if self.path == "/test/declare":
                    result = services.declare()
                elif self.path == "/test/build":
                    result = services.build(body["application_slot_id"], body["topology_artifact_id"])
                elif self.path == "/test/restart_8765":
                    result = services.restart_8765()
                elif self.path == "/test/restart_8080":
                    result = services.restart_8080()
                else:
                    result = {"error": "not found"}
            raw = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            pass

    return Handler


@requires_semantic
def test_semantic_project_applies_only_through_valid_grants(tmp_path, monkeypatch):
    services = Services(tmp_path, monkeypatch)
    keys_8765, keys_8080 = services.transport / route.SERVER_NAME, services.transport / po.SERVER_NAME
    try:
        result = subprocess.run(
            [GODOT, "--headless", "--path", str(SEMANTIC), TEST_SCENE],
            env={**os.environ,
                 "XDG_DATA_HOME": str(tmp_path / "godot_user"),
                 "TRIXEL32D_IT_8080": services.url_8080,
                 "TRIXEL32D_IT_8765": services.url_8765,
                 "TRIXEL32D_IT_CONTROL": services.url_control,
                 "ENGAIN_OPERATOR_ID": "disposable-it-operator",
                 "ENGAIN_OBSERVER_CLIENT_ID": PRESENTER,
                 "ENGAIN_OBSERVER_KEY_FILE": str(keys_8080 / f"{PRESENTER}.key"),
                 "ENGAIN_EXECUTOR_CLIENT_ID": PRESENTER,
                 "ENGAIN_EXECUTOR_KEY_FILE": str(keys_8765 / f"{PRESENTER}.key"),
                 "ENGAIN_TRIXEL32D_GRANT_PUBLIC_KEY_FILE": str(keys_8765 / route.GRANT_PUBLIC_KEY_FILENAME)},
            capture_output=True, text=True, timeout=600,
        )
    finally:
        services.close()

    output = result.stdout + result.stderr
    lines = [line for line in output.splitlines() if "TRIXEL32D_SEMANTIC" in line]
    print("\n".join(lines))
    assert result.returncode == 0 and "TRIXEL32D_SEMANTIC_INTEGRATION_ALL_TESTS=true" in output, output[-8000:]

    # Ledger and evidence agree with what Godot applied.
    events = [json.loads(line) for line in services.ledger.read_text().splitlines()]
    issued = {e["decision_id"]: e for e in events if e["event"] == "authorization_issued"}
    consumed = [e["decision_id"] for e in events if e["event"] == "authorization_consumed"]
    applied = [line.split("=", 1)[1] for line in lines if line.startswith("TRIXEL32D_SEMANTIC_APPLIED_DECISION=")]
    assert len(applied) == 4 and len(set(applied)) == 4
    assert len(consumed) == len(set(consumed)), "a decision was consumed twice"
    assert set(applied) <= set(consumed) <= set(issued)
    for decision_id, event in issued.items():
        receipts = [json.loads(p.read_text()) for p in (services.runtime_root / "trixel32d_reports").glob(
            f"*/{route.RECEIPT_FILENAME}") if json.loads(p.read_text())["authority_ledger_entry"]["decision_id"] == decision_id]
        assert len(receipts) == 1, decision_id
        entry = receipts[0]["authority_ledger_entry"]
        assert (entry["apply_id"], entry["artifact_sha256"], entry["runtime_session_id"]) == (
            event["apply_id"], event["artifact_sha256"], event["runtime_session_id"])
    for path in (services.runtime_root / "trixel32d_reports").glob(f"*/{route.AUTHORIZATION_FILENAME}"):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest in {e["artifact_sha256"] for e in issued.values()}
