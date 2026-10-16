"""
test_snapshot_ownership.py -- Regression tests for the /snapshot ownership
marker that Godot Main.gd checks before it accepts a snapshot.

Main.gd _snapshot_payload_matches_expected_scene accepts a snapshot only when
payload.scene_id and payload.bridge_entities_scene_id both equal the scene it
asked for. The server must set the marker for every scene whose bridge
entities were resolved, including scenes that resolve to zero entities, and
must leave it unset when resolution fails.
"""

from __future__ import annotations

import json
import sys
import threading
import types
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock

from tier2.godotsim import sim_runtime
from tier2.godotsim.http_handlers import RuntimeHTTPHandler
from tier2.godotsim.runtime_core import EngAInRuntime

IDENTITY = {
    "reality_mode": "LIVE",
    "actor_authority_tier": 3,
    "issuer": "godot_semantic_runtime",
    "source": "godot_semantic_runtime",
}

POPULATED_ID = "scene.901_ownership_populated"
EMPTY_ID = "scene.902_ownership_empty"
FAIL_ID = "scene.903_ownership_bridge_fails"
NONLIST_ID = "scene.904_ownership_bridge_nonlist"


def _doc(scene_id, entities):
    # Capitalised words in the text: nothing may turn them into entities.
    text = "Crimson Landing Site. Acknowledged, the Atmospheric Beacon flickers."
    return {
        "scene_id": scene_id,
        "@id": scene_id,
        "entities": entities,
        "events": [{"type": "narration", "data": {"text": text}}],
        "segments": [{"text": text}],
        **IDENTITY,
    }


def _populated_doc():
    return _doc(POPULATED_ID, [
        {"id": "geralt", "name": "Geralt", "type": "character",
         "position": {"x": 0.0, "y": 0.0, "z": 0.0}},
        {"id": "mika", "name": "Mika", "type": "character",
         "position": {"x": 5.0, "y": 0.0, "z": 0.0}},
    ])


def main_gd_accepts(payload, expected):
    """Mirror of Main.gd _snapshot_payload_matches_expected_scene (ids here
    are already canonical, so the canonicalizer is reduced to strip/lower)."""
    canon = lambda v: str(v or "").strip().lower()
    expected = canon(expected)
    scene_id = canon(payload.get("scene_id"))
    owner = canon(payload.get("bridge_entities_scene_id"))
    if not expected or not scene_id or not owner:
        return False
    return scene_id == expected and owner == expected


class TestSnapshotOwnership(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = EngAInRuntime()
        RuntimeHTTPHandler.runtime = cls.runtime
        sim_runtime._install_live_edit_shims(RuntimeHTTPHandler, cls.runtime)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), RuntimeHTTPHandler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read() or b"{}")

    def _load(self, doc):
        status, body = self._call("POST", "/scene/load", doc)
        self.assertEqual((status, body.get("status")), (200, "loaded"))
        return body["scene_id"]

    def _snapshot_payload(self):
        status, env = self._call("GET", "/snapshot")
        self.assertEqual(status, 200)
        return env.get("payload", env)

    def test_populated_scene_is_owned(self):
        loaded = self._load(_populated_doc())
        payload = self._snapshot_payload()
        self.assertEqual(payload.get("scene_id"), loaded)
        self.assertEqual(payload.get("bridge_entities_scene_id"), loaded)
        self.assertEqual(sorted(e["entity_id"] for e in payload["bridge_entities"]),
                         ["geralt", "mika"])
        self.assertTrue(main_gd_accepts(payload, loaded))

    def test_zero_entity_scene_is_owned_and_stays_empty(self):
        loaded = self._load(_doc(EMPTY_ID, []))
        payload = self._snapshot_payload()
        self.assertEqual(payload.get("scene_id"), loaded)
        self.assertEqual(payload.get("bridge_entities"), [])
        self.assertEqual(payload.get("bridge_entities_scene_id"), loaded)
        self.assertTrue(main_gd_accepts(payload, loaded))
        # Polling again gives the same answer.
        self.assertEqual(self._snapshot_payload().get("bridge_entities"), [])

    def test_empty_manifested_list_is_not_filled_from_declared_entities(self):
        doc = dict(_populated_doc(), **{"@entities_manifested": []})
        doc["scene_id"] = doc["@id"] = "scene.905_ownership_manifested_empty"
        loaded = self._load(doc)
        payload = self._snapshot_payload()
        self.assertEqual(payload.get("bridge_entities"), [])
        self.assertEqual(payload.get("bridge_entities_scene_id"), loaded)

    def test_other_scene_snapshot_is_rejected(self):
        populated = self._load(_populated_doc())
        empty = self._load(_doc(EMPTY_ID, []))
        payload = self._snapshot_payload()
        # The populated scene's entities do not leak into the empty scene.
        self.assertEqual(payload.get("bridge_entities"), [])
        self.assertEqual(payload.get("bridge_entities_scene_id"), empty)
        self.assertTrue(main_gd_accepts(payload, empty))
        self.assertFalse(main_gd_accepts(payload, populated))

        self._load(_populated_doc())
        payload = self._snapshot_payload()
        self.assertEqual(payload.get("bridge_entities_scene_id"), populated)
        self.assertFalse(main_gd_accepts(payload, empty))

    def _snapshot_with_bridge(self, scene_doc, bridge_fn):
        fake = types.ModuleType("bridge_integration")
        fake.bridge_entities_for_scene = bridge_fn
        loaded = self._load(scene_doc)
        with mock.patch.dict(sys.modules, {"bridge_integration": fake}):
            payload = self._snapshot_payload()
        return loaded, payload

    def test_bridge_failure_leaves_snapshot_unowned(self):
        def boom(scene, cards):
            raise RuntimeError("bridge down")

        loaded, payload = self._snapshot_with_bridge(_doc(FAIL_ID, []), boom)
        self.assertEqual(payload.get("scene_id"), loaded)
        self.assertNotEqual(payload.get("bridge_entities_scene_id"), loaded)
        self.assertFalse(main_gd_accepts(payload, loaded))

    def test_bridge_non_list_result_leaves_snapshot_unowned(self):
        loaded, payload = self._snapshot_with_bridge(_doc(NONLIST_ID, []),
                                                     lambda scene, cards: None)
        self.assertNotEqual(payload.get("bridge_entities_scene_id"), loaded)
        self.assertFalse(main_gd_accepts(payload, loaded))

    # -- placeholder ids never own a snapshot -------------------------------

    def test_scene_without_id_is_never_owned(self):
        # /scene/load names a doc without an id "scene.unknown".
        for entities in ([], _populated_doc()["entities"], []):
            doc = {k: v for k, v in _doc("", entities).items()
                   if k not in ("scene_id", "@id")}
            loaded = self._load(doc)
            payload = self._snapshot_payload()
            self.assertNotIn("bridge_entities_scene_id", payload)
            self.assertFalse(main_gd_accepts(payload, loaded))
        # The populated id-less scene is not cached and reused for the next one.
        self.assertEqual(payload.get("bridge_entities"), [])

    def test_placeholder_ids_never_own_a_snapshot(self):
        for sid in ("", "unknown", "scene.unknown", "scene.000_unknown", "  Scene.Unknown "):
            scene = {"scene_id": sid, "@id": sid, "entities": []}
            runtime = types.SimpleNamespace(_active_scene_id=sid)
            envelope = {"payload": {"scene_id": sid, "scene": scene,
                                    "bridge_entities_scene_id": sid}}
            sim_runtime._ensure_bridge_entities_in_snapshot(envelope, runtime)
            self.assertNotIn("bridge_entities_scene_id", envelope["payload"], sid)

    # -- the snapshot id alone cannot certify a stale scene ------------------

    def _overlay(self, active_id, payload_id, doc_id, inherited_owner=None):
        scene = {"scene_id": doc_id, "@id": doc_id, "entities": []}
        payload = {"scene_id": payload_id, "scene": scene}
        if inherited_owner is not None:
            payload["bridge_entities_scene_id"] = inherited_owner
        envelope = {"payload": payload}
        sim_runtime._ensure_bridge_entities_in_snapshot(
            envelope, types.SimpleNamespace(_active_scene_id=active_id))
        return envelope["payload"]

    def test_stale_scene_is_not_certified(self):
        fresh, stale = "scene.906_ownership_fresh", "scene.907_ownership_stale"
        self.assertEqual(self._overlay(fresh, fresh, fresh)
                         .get("bridge_entities_scene_id"), fresh)
        cases = {
            "no active scene": (None, stale, stale),
            "snapshot id is not the active scene": (fresh, stale, stale),
            "scene doc is from another scene": (fresh, fresh, stale),
        }
        for name, (active, payload_id, doc_id) in cases.items():
            payload = self._overlay(active, payload_id, doc_id, inherited_owner=payload_id)
            self.assertNotIn("bridge_entities_scene_id", payload, name)
            self.assertFalse(main_gd_accepts(payload, payload_id), name)
            self.assertFalse(main_gd_accepts(payload, fresh), name)

    def test_stale_marker_does_not_survive_a_failed_resolution(self):
        def boom(scene, cards):
            raise RuntimeError("bridge down")

        stale = "scene.907_ownership_stale"
        with mock.patch.dict(sys.modules, {"bridge_integration": types.SimpleNamespace(
                bridge_entities_for_scene=boom)}):
            payload = self._overlay(None, stale, stale, inherited_owner=stale)
        self.assertNotIn("bridge_entities_scene_id", payload)


if __name__ == "__main__":
    unittest.main()
