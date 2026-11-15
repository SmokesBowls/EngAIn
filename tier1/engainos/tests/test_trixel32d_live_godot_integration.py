"""Isolated Godot integration for the live apply path (non-production).

Starts, on loopback ports chosen by the OS and with only disposable data under
tmp_path:
  - a real 8765 scene server, handed a LiveRouteAuthority built by the real
    compose_from_environment() from a disposable two-client policy;
  - a stand-in 8080 runtime serving /snapshot/peek (load stamp + reality context
    + Godot's reported presentation observation), plus /test/* controls.

It then runs the headless Godot test
`trixel_proof/trixel32d_apply_executor/tests/test_trixel32d_live_apply_integration.gd`
in the godotollama project, which applies geometry only through `apply_live`.

Skipped when the Godot binary or the godotollama project is not present.
Production state is never touched: the production policy file is not read,
and every runtime path is under tmp_path.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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

GODOT = shutil.which(os.environ.get("GODOT_BIN", "godot"))
GODOTOLLAMA = Path(os.environ.get("GODOTOLLAMA_ROOT", "/mnt/data-drive/godotollama"))
GODOT_TEST = "res://trixel_proof/trixel32d_apply_executor/tests/test_trixel32d_live_apply_integration.gd"

pytestmark = pytest.mark.skipif(
    GODOT is None or not (GODOTOLLAMA / "project.godot").is_file()
    or not (GODOTOLLAMA / GODOT_TEST.removeprefix("res://")).is_file(),
    reason="Godot binary or godotollama live-apply integration test not available",
)

BUILDER, PRESENTER = "integration-builder", "integration-presenter"
SLOTS = [f"slot-a{i}" for i in range(1, 7)]
PARENT = ("RUNTIME_CONTAINER", "container-terrain-live")


class FakeRuntime:
    """Stand-in 8080: the load stamp, reality context and Godot report a real runtime would publish."""

    def __init__(self, truth_path: Path, runtime_root: Path):
        self.truth_path = truth_path
        self.runtime_root = runtime_root
        self.load_seq = 0
        self.scene_id = ""
        self.observation = None
        self.builder_secret = b""
        self.url_8765 = ""
        self.lock = threading.Lock()
        self.load("scene-it-primary")

    def load(self, scene_id):
        with self.lock:
            self.load_seq += 1
            self.scene_id = scene_id
            self.truth_path.write_text(json.dumps({
                "scene_id": scene_id,
                "declared_targets": [[*PARENT, slot] for slot in SLOTS],
                "slot_occupancy": {},
            }))

    def peek(self):
        with self.lock:
            scene = {"scene_id": self.scene_id, "segments": [{"text": "integration"}], "entities": []}
            return {
                "payload": {
                    "scene_id": self.scene_id,
                    "scene": scene,
                    "scene_activation": {"runtime_instance_id": "it-runtime", "load_seq": self.load_seq,
                                         "scene_id": self.scene_id},
                },
                "reality_context": {"mode": "DRAFT", "scene_id": None},
                "presentation_observation": self.observation,
            }

    def build(self, slot_id, topology_artifact_id):
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
        req = urllib.request.Request(
            self.url_8765 + route.ROUTE_PATH, data=body, method="POST",
            headers={"Content-Type": "application/json",
                     **signed_headers(BUILDER, self.builder_secret, "POST", route.ROUTE_PATH, body)},
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                code, result = resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as err:
            code, result = err.code, json.loads(err.read() or b"{}")
        out = {"code": code, "body": result}
        if code == 200:
            out["authorization_path"] = str(self.runtime_root.parent / result["authorization_file"])
            out["payload_path"] = str(self.runtime_root.parent / result["built_drop_dir"] / route.PAYLOAD_FILENAME)
        return out


def _runtime_handler(runtime: FakeRuntime):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, data, status=200):
            raw = json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.path == "/snapshot/peek":
                return self._send(runtime.peek())
            self._send({"error": "not found"}, 404)

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if self.path == "/test/load":
                runtime.load(body["scene_id"])
                return self._send(runtime.peek()["payload"]["scene_activation"])
            if self.path == "/test/observation":
                with runtime.lock:
                    runtime.observation = body
                return self._send({"ok": True})
            if self.path == "/test/build":
                return self._send(runtime.build(body["application_slot_id"], body["topology_artifact_id"]))
            self._send({"error": "not found"}, 404)

        def log_message(self, *args):
            pass

    return Handler


def _serve(server):
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}"


def test_godot_applies_only_through_a_valid_one_time_grant(tmp_path, monkeypatch):
    runtime_root = tmp_path / "runtime"
    truth = tmp_path / "scene_truth.json"
    monkeypatch.setattr(route, "RUNTIME_DIR", runtime_root)
    monkeypatch.setattr(route, "SCENE_TRUTH_PATH", truth)
    monkeypatch.setenv(route.FLAG_ENV, "1")  # this test process only; servers are disposable

    fake = FakeRuntime(truth, runtime_root)
    runtime_server = ThreadingHTTPServer(("127.0.0.1", 0), _runtime_handler(fake))
    runtime_url = _serve(runtime_server)
    monkeypatch.setenv(route.RUNTIME_URL_ENV, runtime_url)

    def observation_source():
        # Godot's report, read back from the runtime: never from the 8765 caller.
        with urllib.request.urlopen(runtime_url + "/snapshot/peek", timeout=10) as resp:
            return json.loads(resp.read()).get("presentation_observation")

    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"contract": "engainos.local_client_policy.v1", "clients": {
        BUILDER: {"actor_id": "disposable-integration-builder", "actor_authority_tier": 2, "routes": ["build"]},
        PRESENTER: {"routes": ["consume"]},
    }}))
    transport = tmp_path / "transport"
    ledger = runtime_root / "ledger.jsonl"
    authority, why = route.compose_from_environment(
        observation_source=observation_source, ledger_path=ledger, policy_path=policy, transport_dir=transport,
    )
    assert authority is not None, why
    keys = transport / route.SERVER_NAME
    fake.builder_secret = bytes.fromhex((keys / f"{BUILDER}.key").read_text())
    monkeypatch.setattr(scene_server.SceneRequestHandler, "trixel32d_authority", authority)
    authority_server = ThreadingHTTPServer(("127.0.0.1", 0), scene_server.SceneRequestHandler)
    fake.url_8765 = _serve(authority_server)

    try:
        result = subprocess.run(
            [GODOT, "--headless", "--path", str(GODOTOLLAMA), "-s", GODOT_TEST],
            env={**os.environ,
                 "TRIXEL32D_IT_8765": fake.url_8765,
                 "TRIXEL32D_IT_8080": runtime_url,
                 "TRIXEL32D_IT_CLIENT_ID": PRESENTER,
                 "TRIXEL32D_IT_CLIENT_KEY_FILE": str(keys / f"{PRESENTER}.key"),
                 "TRIXEL32D_IT_GRANT_PUBLIC_KEY_FILE": str(keys / route.GRANT_PUBLIC_KEY_FILENAME)},
            capture_output=True, text=True, timeout=300,
        )
    finally:
        authority_server.shutdown()
        authority_server.server_close()
        runtime_server.shutdown()
        runtime_server.server_close()
        authority.close()

    output = result.stdout + result.stderr
    lines = [line for line in output.splitlines() if "TRIXEL32D_LIVE_INTEGRATION" in line]
    print("\n".join(lines))
    assert result.returncode == 0 and "TRIXEL32D_LIVE_INTEGRATION_ALL_TESTS=true" in output, output[-6000:]
    assert not [line for line in lines if line.endswith("FALSE") or "] FALSE " in line]

    # The ledger agrees with Godot: every application was preceded by exactly one consumption.
    events = [json.loads(line) for line in ledger.read_text().splitlines()]
    consumed = [e["decision_id"] for e in events if e["event"] == "authorization_consumed"]
    assert len(consumed) == len(set(consumed))
    assert all(e["event"] in {"authorization_issued", "authorization_consumed"} for e in events)
