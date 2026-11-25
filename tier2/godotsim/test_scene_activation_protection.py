"""
test_scene_activation_protection.py -- T03-R3: an active scene is replaced only by a request
naming its exact activation stamp, on every activation path (/scene/load, queued scene
commands, bulk loading), and a simulation step never interleaves with a replacement.

Isolated runtimes; the simulation loop is disabled except where the tick boundary is tested,
so state comparisons are exact. Fixture scene documents only.
"""

from __future__ import annotations

import copy
import json
import os
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock

from tier2.godotsim import runtime_core, sim_runtime
from tier2.godotsim.http_handlers import RuntimeHTTPHandler
from tier2.godotsim.scene_manager import SceneActivationConflict, SceneManager
from tier2.godotsim.vault_manager import bulk_load_scenes

IDENTITY = {"reality_mode": "DRAFT", "actor_authority_tier": 2,
            "actor_id": "t03r3-test", "source_system": "t03r3-test"}


def _doc(scene_id, marker="a"):
    return {
        "scene_id": scene_id, "@id": scene_id,
        "entities": [
            {"id": "geralt", "name": "Geralt", "type": "character", "health": 100.0, "max_health": 100.0,
             "position": {"x": 0.0, "y": 0.0, "z": 0.0}},
            {"id": "mika", "name": "Mika", "type": "character", "health": 80.0, "max_health": 80.0,
             "position": {"x": 5.0, "y": 0.0, "z": 0.0}},
        ],
        "segments": [{"text": f"segment {marker}"}],
        "layout_proof": {"marker": marker},
    }


A, B, C = "scene.900_activation_a", "scene.900_activation_b", "scene.900_activation_c"


class _Runtime:
    """An isolated runtime behind a real threaded 8080 handler."""

    def __init__(self, loop=False):
        if loop:
            self.rt = runtime_core.EngAInRuntime()
        else:
            with mock.patch.object(runtime_core.EngAInRuntime, "_simulation_loop", lambda self: None):
                self.rt = runtime_core.EngAInRuntime()
        self.saved = getattr(RuntimeHTTPHandler, "runtime", None)
        RuntimeHTTPHandler.runtime = self.rt
        sim_runtime._install_live_edit_shims(RuntimeHTTPHandler, self.rt)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), RuntimeHTTPHandler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.rt.running = False
        RuntimeHTTPHandler.runtime = self.saved

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read() or b"{}")

    def load(self, scene_id, marker="a", **extra):
        return self.call("POST", "/scene/load", {"scene": _doc(scene_id, marker), **IDENTITY, **extra})

    @property
    def stamp(self):
        return self.rt.scene_manager.current_activation()

    def state(self):
        """Everything an activation replaces, plus the registry and the active pointer."""
        snap = self.rt.snapshot
        keys = ("scene", "scene_raw", "scene_id", "scene_activation", "entities", "spatial", "perception",
                "behavior", "events", "bridge_entities", "bridge_entities_scene_id")
        combat = self.rt.combat
        return copy.deepcopy({
            "snapshot": {k: snap.get(k) for k in keys},
            "registry": {sid: info["raw"] for sid, info in self.rt.scene_manager.scenes.items()},
            "active": (getattr(self.rt, "_active_scene_id", None), getattr(self.rt, "_active_scene_doc", None)),
            "load_seq": self.rt.scene_load_seq,
            "combat": {k: getattr(combat, k) for k in ("active_combats", "damage_queue", "entity_armor",
                                                       "entity_hp", "pending_damage")} if combat else None,
        })


class TestSceneActivationProtection(unittest.TestCase):
    def setUp(self):
        self.r = _Runtime()

    def tearDown(self):
        self.r.close()

    def _refused(self, status, body, http, reason, active):
        self.assertEqual((status, body.get("error"), body.get("reason")), (http, "scene_activation_conflict", reason))
        self.assertEqual(body.get("active_scene_activation"), active)

    # -- /scene/load ----------------------------------------------------------

    def test_empty_runtime_accepts_and_returns_the_new_stamp(self):
        status, body = self.r.load(A)
        self.assertEqual((status, body["status"]), (200, "loaded"))
        self.assertEqual(body["scene_activation"], self.r.stamp)
        self.assertEqual(self.r.stamp["scene_id"], A)
        _, env = self.r.call("GET", "/snapshot/peek")
        self.assertEqual(env["payload"]["scene_activation"], body["scene_activation"])

    def test_unintended_replacement_is_refused_without_side_effects(self):
        self.r.load(A)
        before = self.r.state()
        for extra in ({}, {"expected_scene_activation": None}):
            status, body = self.r.load(B, "b", **extra)
            self._refused(status, body, 409, "scene_activation_required", before["snapshot"]["scene_activation"])
            self.assertEqual(self.r.state(), before)
            self.assertNotIn(B, self.r.rt.scene_manager.scenes)

    def test_matching_stamp_replaces_and_issues_a_new_stamp(self):
        _, first = self.r.load(A)
        status, body = self.r.load(B, "b", expected_scene_activation=first["scene_activation"])
        self.assertEqual(status, 200)
        new = body["scene_activation"]
        self.assertEqual((new["scene_id"], new["load_seq"]), (B, first["scene_activation"]["load_seq"] + 1))
        self.assertEqual(new["runtime_instance_id"], first["scene_activation"]["runtime_instance_id"])
        self.assertEqual(self.r.rt._active_scene_id, B)
        self.assertEqual(self.r.rt.snapshot["scene"]["segments"], [{"text": "segment b"}])

    def test_stale_stamps_are_refused_without_side_effects(self):
        _, first = self.r.load(A)
        _, second = self.r.load(B, "b", expected_scene_activation=first["scene_activation"])
        current = second["scene_activation"]
        before = self.r.state()
        for stale in (first["scene_activation"],                                   # obsolete load_seq
                      dict(current, runtime_instance_id="another-runtime"),        # other runtime
                      dict(current, scene_id=A),                                   # other scene
                      dict(current, load_seq=current["load_seq"] + 1)):            # future load
            status, body = self.r.load(C, "c", expected_scene_activation=stale)
            self._refused(status, body, 409, "stale_scene_activation", current)
            self.assertEqual(self.r.state(), before)
            self.assertNotIn(C, self.r.rt.scene_manager.scenes)

    def test_malformed_stamps_are_refused_without_side_effects(self):
        _, first = self.r.load(A)
        good = first["scene_activation"]
        before = self.r.state()
        for bad in ({k: v for k, v in good.items() if k != "load_seq"}, dict(good, extra=1),
                    dict(good, load_seq=True), dict(good, load_seq=str(good["load_seq"])),
                    dict(good, runtime_instance_id=""), [good], "stamp", 1):
            status, body = self.r.load(B, "b", expected_scene_activation=bad)
            self._refused(status, body, 400, "invalid_expected_scene_activation", good)
            self.assertEqual(self.r.state(), before)

    def test_stamp_against_an_empty_runtime_is_refused(self):
        before = self.r.state()
        fake = {"runtime_instance_id": self.r.rt.runtime_instance_id, "load_seq": 1, "scene_id": A}
        status, body = self.r.load(A, expected_scene_activation=fake)
        self._refused(status, body, 409, "no_active_scene", None)
        self.assertEqual(self.r.state(), before)

    def test_reloading_the_same_scene_needs_its_stamp(self):
        _, first = self.r.load(A)
        before = self.r.state()
        status, body = self.r.load(A, "a2")
        self._refused(status, body, 409, "scene_activation_required", first["scene_activation"])
        self.assertEqual(self.r.state(), before)
        status, body = self.r.load(A, "a2", expected_scene_activation=first["scene_activation"])
        self.assertEqual(status, 200)
        self.assertEqual(body["scene_activation"]["load_seq"], first["scene_activation"]["load_seq"] + 1)

    def test_competing_replacements_of_one_activation_cannot_both_succeed(self):
        _, first = self.r.load(A)
        stamp, n = first["scene_activation"], 8
        gate, results = threading.Barrier(n), []

        def race(i):
            gate.wait()
            results.append(self.r.load(f"scene.900_race_{i}", str(i), expected_scene_activation=stamp))

        threads = [threading.Thread(target=race, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(30)
        winners = [body for status, body in results if status == 200]
        self.assertEqual(len(results), n)
        self.assertEqual(len(winners), 1)
        for status, body in results:
            if status != 200:
                self._refused(status, body, 409, "stale_scene_activation", winners[0]["scene_activation"])
        self.assertEqual(self.r.stamp, winners[0]["scene_activation"])
        self.assertEqual(self.r.stamp["load_seq"], stamp["load_seq"] + 1)
        raced = [sid for sid in self.r.rt.scene_manager.scenes if sid.startswith("scene.900_race_")]
        self.assertEqual(raced, [winners[0]["scene_id"]])  # losers registered nothing

    # -- queued scene commands ------------------------------------------------

    def test_queued_select_scene_follows_the_same_contract(self):
        self.r.load(A)
        self.r.rt.scene_manager.load_scene(_doc(B, "b"), activate=False)  # registration of a non-active scene
        before = self.r.state()
        self.r.rt.add_command({"command": "select_scene", "scene_id": B})
        self.r.rt.drain_commands()
        self.assertEqual(self.r.state(), before)
        self.r.rt.add_command({"command": "select_scene", "scene_id": B, "expected_scene_activation": self.r.stamp})
        self.r.rt.drain_commands()
        self.assertEqual((self.r.stamp["scene_id"], self.r.rt._active_scene_id), (B, B))

    def test_queued_load_scene_from_file_follows_the_same_contract(self):
        self.r.load(A)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "b.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(_doc(B, "b"), f)
            before = self.r.state()
            self.r.rt.add_command({"command": "load_scene_from_file", "path": path})
            self.r.rt.drain_commands()
            self.assertEqual(self.r.state(), before)
            self.assertNotIn(B, self.r.rt.scene_manager.scenes)
            self.r.rt.add_command({"command": "load_scene_from_file", "path": path,
                                   "expected_scene_activation": self.r.stamp})
            self.r.rt.drain_commands()
            self.assertEqual(self.r.stamp["scene_id"], B)

    # -- bulk loading ---------------------------------------------------------

    def _bulk(self, docs):
        with tempfile.TemporaryDirectory() as tmp:
            for i, doc in enumerate(docs):
                with open(os.path.join(tmp, f"{i}.json"), "w", encoding="utf-8") as f:
                    json.dump(doc, f)
            return bulk_load_scenes(self.r.rt, tmp)

    def test_bulk_loading_activates_only_an_empty_runtime(self):
        stats = self._bulk([_doc(A), _doc(B, "b")])
        self.assertTrue(stats["default_scene_selected"])
        self.assertEqual(self.r.stamp["scene_id"], A)  # first sorted id
        self.assertEqual(self.r.stamp["load_seq"], 1)

    def test_bulk_loading_keeps_the_active_scene_and_cannot_rewrite_its_document(self):
        self.r.load(A)
        before = self.r.state()
        stats = self._bulk([_doc(A, "rewritten"), _doc(C, "c")])
        self.assertEqual((stats["default_scene_selected"], stats["default_scene_reason"]),
                         (False, "kept_existing_active"))
        self.assertTrue(any("active_scene_document_is_immutable" in e for e in stats["errors"]))
        after = self.r.state()
        self.assertIn(C, after["registry"])           # other scenes still register
        after["registry"].pop(C)
        self.assertEqual(after, before)               # active scene, its document and stamp untouched

    def test_registration_alone_cannot_rewrite_the_active_document(self):
        self.r.load(A)
        before = self.r.state()
        with self.assertRaises(SceneActivationConflict) as ctx:
            self.r.rt.scene_manager.load_scene(_doc(A, "rewritten"), activate=False)
        self.assertEqual(ctx.exception.reason, "active_scene_document_is_immutable")
        self.assertEqual(self.r.state(), before)


class TestTickBoundary(unittest.TestCase):
    """With the real simulation loop: no tick runs while an activation is in progress."""

    def test_no_tick_interleaves_with_an_activation(self):
        r = _Runtime(loop=True)
        in_activation = threading.Event()
        overlaps, ticks = [], []
        real_tick = r.rt.tick
        real_bridge = SceneManager._bridge_entities_for_scene

        def tick(*a, **kw):
            ticks.append(in_activation.is_set())
            if in_activation.is_set():
                overlaps.append(time.monotonic())
            return real_tick(*a, **kw)

        def slow_bridge(manager):
            in_activation.set()  # mid-activation: state already cleared, stamp not yet issued
            time.sleep(0.25)
            in_activation.clear()
            return real_bridge(manager)

        try:
            r.rt.tick = tick
            with mock.patch.object(SceneManager, "_bridge_entities_for_scene", slow_bridge):
                time.sleep(0.1)
                status, first = r.load(A)
                self.assertEqual(status, 200)
                status, _ = r.load(B, "b", expected_scene_activation=first["scene_activation"])
                self.assertEqual(status, 200)
                time.sleep(0.1)
        finally:
            r.close()
        self.assertGreater(len(ticks), 10)  # the loop really ran around the activations
        self.assertEqual(overlaps, [])


if __name__ == "__main__":
    unittest.main()
