#!/usr/bin/env python3
"""http_handlers.py - HTTP transport for EngAIn Runtime.

Pure HTTP routing. Delegates all logic to:
    - CommandDispatcher for /command
    - SceneManager (via runtime.scene_manager) for scene/vault operations
    - EngAInRuntime for snapshots and subsystem state

No game logic lives here. If a patch breaks this file, only HTTP dies — the engine keeps running.
"""

import json
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict, TYPE_CHECKING
from urllib.parse import parse_qs, unquote, urlparse

import engain_hooks

from vault_manager import (
    normalize_scene_doc,
    parse_manifest_v1,
    bulk_load_scenes,
    get_vault_fingerprint,
    get_build_state,
    save_build_state,
    write_quarantine_marker,
    rsync_mirror,
    chmod_readonly,
    _count_files,
    _safe_mkdir,
    _run,
)
from command_dispatcher import CommandDispatcher

try:
    _ROOT_FOR_SCENE_ID = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _ROOT_FOR_SCENE_ID not in sys.path:
        sys.path.insert(0, _ROOT_FOR_SCENE_ID)
    from mettaext.scene_identity import canonical_scene_id
except Exception:
    def canonical_scene_id(raw):
        return str(raw or "unknown")

if TYPE_CHECKING:
    from runtime_core import EngAInRuntime


# ── Locate project root ─────────────────────────────────────────

def _find_root_dir(start_dir: str) -> str:
    cur = os.path.abspath(start_dir)
    for _ in range(8):
        if os.path.exists(os.path.join(cur, "engain_ingest.py")) or os.path.isdir(os.path.join(cur, "mettaext")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.dirname(os.path.abspath(start_dir))


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = _find_root_dir(THIS_DIR)


# ── JSON Encoder ─────────────────────────────────────────────────

class SafeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (set, tuple)):
            return list(obj)
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


# ── HTTP Handler ─────────────────────────────────────────────────

class RuntimeHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for EngAIn runtime. Delegates all logic to engine components."""

    runtime: 'EngAInRuntime' = None  # Injected at server startup

    def _send_json(self, status_code: int, data: Dict[str, Any]):
        try:
            payload = json.dumps(data, cls=SafeJSONEncoder).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as e:
            print(f"Serialization Error: {e}")

    # ── GET Endpoints ────────────────────────────────────────────

    def do_GET(self):
        parsed_url = urlparse(self.path)
        base_path = parsed_url.path.rstrip("/")
        params = {k: v[0] for k, v in parse_qs(parsed_url.query).items()}

        if base_path in ("", "/health", "/status"):
            data = {"ok": True, "service": "engain", "ts": int(time.time()), "pid": os.getpid()}
            return self._send_json(200, data)

        elif base_path == "/snapshot":
            envelope = self.runtime.get_snapshot()
            return self._send_json(200, envelope)

        elif base_path == "/transforms":
            return self._handle_transforms()

        elif base_path == "/embodiment/pending":
            return self._handle_embodiment_pending()

        elif base_path.startswith("/environment/terrain/"):
            scene_id = unquote(base_path[len("/environment/terrain/"):])
            return self._handle_environment_terrain(scene_id)

        elif base_path == "/vault/status":
            status = self.runtime.vault_linker.get_status()
            status["vault_scenes_registered"] = len(self.runtime.vault_scenes)
            return self._send_json(200, status)

        elif base_path == "/vault/search":
            q = params.get("q", "")
            limit_str = params.get("limit", "20")
            mode = params.get("mode", "all")
            try:
                limit = int(limit_str)
            except Exception:
                limit = 20

            # Allow empty q to list all scenes
            return self._handle_vault_search(q, limit, mode)

        return self._send_json(404, {"error": "not found", "path": self.path})

    # ── POST Endpoints ───────────────────────────────────────────

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length)
        print(f"[HTTP POST] {self.path} ({len(body_raw)} bytes)")

        try:
            if not body_raw:
                return self._send_json(400, {"type": "error", "error": "empty_body"})
            body = json.loads(body_raw.decode("utf-8"))

            # Wrap with instrumentation
            roots = [ROOT_DIR]
            runtime_hook = engain_hooks.HookRuntime(roots, enable_profiling=True)

            def _dispatch_and_respond():
                if self.path == "/command":
                    return self._handle_command(body)
                elif self.path == "/scene/load":
                    return self._handle_scene_load(body)
                elif self.path == "/vault/link":
                    return self._handle_vault_link(body)
                elif self.path == "/world/sync":
                    return self._handle_world_sync(body)
                elif self.path == "/world/load_mirror":
                    return self._handle_world_load_mirror(body)
                elif self.path == "/transforms":
                    return self._handle_transforms()
                elif self.path == "/embodiment/apply":
                    return self._handle_embodiment_apply(body)

                # Legacy adapter paths
                if self.path in ("/combat/damage", "/inventory/take", "/inventory/drop", "/inventory/wear", "/dialogue/ask"):
                    if isinstance(body, dict):
                        body["command"] = self.path.lstrip("/")
                    return self._handle_command(body)

                return self._send_json(404, {"type": "error", "error": "not_found", "path": self.path})

            # Intercept for debug chain injection
            orig_send_json = self._send_json

            def _wrapped_send_json(code, data):
                if isinstance(data, dict):
                    data.setdefault("debug", {})
                    data["debug"]["chain"] = engain_hooks.get_chain()
                return orig_send_json(code, data)

            self._send_json = _wrapped_send_json
            try:
                runtime_hook.run(_dispatch_and_respond)
            finally:
                self._send_json = orig_send_json

        except json.JSONDecodeError as e:
            self._send_json(400, {"type": "error", "error": "invalid_json", "detail": str(e)})
        except Exception as e:
            print(f"[HTTP POST] Server Error: {e}")
            traceback.print_exc()
            self._send_json(500, {"type": "error", "error": "internal_server_error", "message": str(e)})

    # ── GET Handler Implementations ──────────────────────────────

    def _handle_environment_terrain(self, scene_id: str):
        """Return generated terrain metadata for a scene, if available."""
        env_manager = getattr(self.runtime, "env_manager", None)
        if env_manager:
            generated_terrains = getattr(env_manager, "generated_terrains", None)
            if isinstance(generated_terrains, dict):
                terrain_data = generated_terrains.get(scene_id)
                if terrain_data:
                    return self._send_json(200, terrain_data)

        return self._send_json(200, {"status": "not_found"})

    # ── POST Handler Implementations ─────────────────────────────

    def _handle_embodiment_apply(self, body: Dict[str, Any]):
        """
        Apply a Trixel Embodiment Contract to the Godot client queue.

        Flow:
            Trixel recipe generation -> embodiment contract -> this endpoint -> Godot SemanticRenderer
        """
        if not isinstance(body, dict):
            return self._send_json(400, {"error": "Contract must be a dictionary"})

        if body.get("contract_version") != "trixel_embodiment.v1":
            return self._send_json(400, {"error": "Invalid contract version"})

        contracts = getattr(self.runtime, "pending_embodiment_contracts", None)
        if not isinstance(contracts, list):
            self.runtime.pending_embodiment_contracts = []
            contracts = self.runtime.pending_embodiment_contracts

        lock = getattr(self.runtime, "pending_embodiment_contracts_lock", None)
        if lock is None:
            self.runtime.pending_embodiment_contracts_lock = threading.Lock()
            lock = self.runtime.pending_embodiment_contracts_lock

        with lock:
            contracts.append(body)

        return self._send_json(200, {
            "status": "accepted",
            "scene_id": body.get("scene_id"),
            "terrain_profile": body.get("materialization", {}).get("terrain_profile"),
        })

    def _handle_embodiment_pending(self):
        """Return and consume the next pending Trixel Embodiment Contract."""
        contracts = getattr(self.runtime, "pending_embodiment_contracts", None)
        if not isinstance(contracts, list):
            self.runtime.pending_embodiment_contracts = []
            contracts = self.runtime.pending_embodiment_contracts

        lock = getattr(self.runtime, "pending_embodiment_contracts_lock", None)
        if lock is None:
            self.runtime.pending_embodiment_contracts_lock = threading.Lock()
            lock = self.runtime.pending_embodiment_contracts_lock

        with lock:
            contract = contracts.pop(0) if contracts else None
            remaining = len(contracts)

        return self._send_json(200, {
            "status": "ok" if isinstance(contract, dict) else "empty",
            "contract": contract,
            "remaining": remaining,
        })

    def _handle_command(self, body: Dict[str, Any]):
        if not isinstance(body, dict):
            return self._send_json(400, {"type": "error", "error": "body_not_object"})

        from runtime_gateway import RuntimeGateway
        dispatcher = CommandDispatcher(self.runtime, self.runtime.scene_manager)
        decision = RuntimeGateway(self.runtime, dispatcher).submit(body)

        if not decision.accepted:
            return self._send_json(decision.status_code, {
                "type": "error",
                "error": "governance_rejected",
                "reason": decision.reason,
                "command_id": decision.command_id,
                "reality_mode": decision.reality_mode,
            })

        result = decision.result

        # Failsafe: if dispatch queued a mutation but the sim thread isn't running,
        # drain once right here so snapshot updates immediately.
        try:
            if isinstance(result, dict) and result.get("status") == "queued":
                sim_thread = getattr(self.runtime, "sim_thread", None)
                sim_alive = bool(sim_thread and callable(getattr(sim_thread, "is_alive", None)) and sim_thread.is_alive())

                if not sim_alive:
                    drain = getattr(self.runtime, "drain_commands", None)
                    if callable(drain):
                        drain()
        except Exception:
            traceback.print_exc()

        return self._send_json(200, result)

    def _handle_scene_load(self, body: Dict[str, Any]):
        if not isinstance(body, dict):
            return self._send_json(400, {"type": "error", "error": "body_not_object"})

        doc = body.get("zonj") or body.get("scene")
        if not doc:
            doc = {k: v for k, v in body.items() if k not in ("command", "action")}

        # Vault fallback: if only an ID, look up in vault_scenes
        has_segments = "segments" in doc or "=segments" in doc
        if not has_segments and self.runtime.vault_scenes:
            req_id = doc.get("scene_id") or doc.get("@id") or body.get("scene_id")
            if req_id in self.runtime.vault_scenes:
                doc = self.runtime.vault_scenes[req_id]

        doc = normalize_scene_doc(doc)
        has_id = doc.get("scene_id") or doc.get("@id") or (doc.get("type") == "scene" and doc.get("id"))
        has_segments = "segments" in doc or "=segments" in doc

        if not (has_id and has_segments):
            print("[HTTP] ERROR: Invalid ZONJ doc sent to /scene/load")
            return self._send_json(400, {
                "type": "error",
                "error": "invalid_zonj",
                "message": "Missing required fields: scene_id (or id) and segments",
            })

        # Governance: identity required; REPLAY blocks scene load; FINALIZED requires Tier 3.
        from runtime_gateway import (
            _extract_request_context, _get_global_context, _CORE_DIR,
            _missing_identity_fields,
        )
        import sys as _sys
        if _CORE_DIR not in _sys.path:
            _sys.path.insert(0, _CORE_DIR)
        from intent_shadow import record_intent as _record_intent
        from canon import can_edit as _can_edit

        _req_ctx, _tier, _issuer, _source = _extract_request_context(body)
        _target_scene_id = canonical_scene_id(doc.get("@id") or doc.get("scene_id") or "unknown")

        _identity_error = _missing_identity_fields(body)
        if _identity_error:
            _record_intent(issuer=_issuer, command=body, reason_rejected=_identity_error,
                           scene_id=_target_scene_id, source=_source)
            return self._send_json(400, {"type": "error", "error": "governance_rejected",
                                         "reason": _identity_error})

        _global_ctx = _get_global_context()

        if not _global_ctx.allows_mutation():
            _record_intent(issuer=_issuer, command=body, reason_rejected="REPLAY mode — scene load blocked",
                           scene_id=_target_scene_id, source=_source)
            return self._send_json(403, {"type": "error", "error": "governance_rejected",
                                         "reason": "REPLAY mode — scene load blocked"})

        if not _req_ctx.allows_mutation():
            _record_intent(issuer=_issuer, command=body, reason_rejected="Request declares REPLAY — scene load blocked",
                           scene_id=_target_scene_id, source=_source)
            return self._send_json(403, {"type": "error", "error": "governance_rejected",
                                         "reason": "Request declares REPLAY — scene load blocked"})

        if not _can_edit(_target_scene_id) and _tier < 3:
            _record_intent(issuer=_issuer, command=body,
                           reason_rejected=f"Scene '{_target_scene_id}' is FINALIZED — requires Tier 3",
                           scene_id=_target_scene_id, authority_tier=_tier, source=_source)
            return self._send_json(403, {"type": "error", "error": "governance_rejected",
                                         "reason": f"Scene '{_target_scene_id}' is FINALIZED — requires Tier 3 authority"})

        # Load with activate=True so snapshot gets updated
        self.runtime.scene_manager.load_scene(doc, activate=True)
        scene_id = canonical_scene_id(doc.get("@id") or doc.get("scene_id") or "unknown")

        # Trigger terrain generation (non-blocking).
        # This handler runs under ThreadingHTTPServer, not an asyncio server, so
        # schedule the coroutine in a daemon thread instead of asyncio.create_task().
        scene_data = body.get("scene_data", doc)
        env_manager = getattr(self.runtime, "env_manager", None)
        if hasattr(self.runtime, "env_manager") and env_manager:
            def _run_scene_environment_generation():
                try:
                    import asyncio
                    asyncio.run(
                        env_manager.generate_scene_environment(scene_id, scene_data)
                    )
                except Exception as e:
                    print(f"[HTTP] Scene environment generation failed: {e}")
                    traceback.print_exc()

            threading.Thread(target=_run_scene_environment_generation, daemon=True).start()
        # [SCENE-LOAD-PERSIST-ACTIVE V2]
        try:
            # Persist active scene so /snapshot can hydrate reliably
            self.runtime._active_scene_id = scene_id
            self.runtime._active_scene_doc = doc
            
            # Persist to config so it survives restart
            from sim_runtime import save_vault_config
            _, vault_root, manifest_path = self._get_active_vault_context()
            config_path = getattr(self.runtime, '_config_path', None)
            if config_path and vault_root and manifest_path:
                save_vault_config(config_path, vault_root, manifest_path, scene_id)
        except Exception as e:
            print(f"[HTTP] Failed to persist active scene state: {e}")

        return self._send_json(200, {
            "type": "result",
            "action": "scene/load",
            "scene_id": scene_id,
            "status": "loaded",
        })

    def _get_active_vault_context(self):
        snapshot = getattr(self.runtime, "snapshot", None)
        if not isinstance(snapshot, dict):
            return None, None, None

        active_id = snapshot.get("active_vault_id")
        vaults = snapshot.get("vaults")
        if not active_id or not isinstance(vaults, dict):
            return active_id, None, None

        entry = vaults.get(active_id)
        if not isinstance(entry, dict):
            return active_id, None, None

        return active_id, entry.get("vault_root"), entry.get("manifest_path")

    def _handle_vault_link(self, body: Dict[str, Any]):
        manifest = body.get("manifest")
        vault_root = body.get("vault_root")
        if not manifest or not vault_root:
            return self._send_json(400, {"status": "error", "error": "need manifest + vault_root"})

        result = self.runtime.vault_linker.link(manifest, vault_root)

        manifest_path = body.get("manifest_path")
        if not manifest_path:
            candidate = os.path.join(vault_root, "vault.manifest.json")
            if os.path.isfile(candidate):
                manifest_path = candidate

        if result.get("status") == "ok":
            loaded = 0
            for sid, scene in self.runtime.vault_linker.get_all_scenes().items():
                self.runtime.vault_scenes[sid] = scene
                loaded += 1
            result["scenes_registered"] = loaded

            vault_id = (
                result.get("vault_id")
                or body.get("vault_id")
                or (manifest.get("vault_id") if isinstance(manifest, dict) else None)
                or (manifest.get("id") if isinstance(manifest, dict) else None)
                or os.path.basename(os.path.abspath(vault_root))
            )
            snapshot = getattr(self.runtime, "snapshot", None)
            if isinstance(snapshot, dict) and vault_id:
                vaults = snapshot.setdefault("vaults", {})
                if isinstance(vaults, dict):
                    vaults[vault_id] = {
                        "vault_root": vault_root,
                        "manifest_path": manifest_path,
                    }
                snapshot["active_vault_id"] = vault_id

        self._send_json(200, result)
        from sim_runtime import save_vault_config
        config_path = getattr(self.runtime, '_config_path', None)
        active_sid = getattr(self.runtime, '_active_scene_id', None)
        if config_path and vault_root and manifest_path:
            save_vault_config(config_path, vault_root, manifest_path, active_sid)

    def _handle_vault_search(self, query: str, limit: int = 20, mode: str = "all"):
        if not self.runtime.vault_scenes:
            return self._send_json(200, {"query": query, "hits": [], "count": 0, "error": "no vault linked"})

        q = query.lower()
        hits = []
        for sid, scene in self.runtime.vault_scenes.items():
            where = scene.get("where", "") or ""
            if mode == "playable" and not (
                where.startswith("Book 1") or where.startswith("Book 2") or where.startswith("Book 3")
            ):
                continue

            score = 0
            context = ""
            if q in sid.lower():
                score += 10

            entities = scene.get("@entities") or scene.get("entities", [])
            for ent in entities:
                name = ent if isinstance(ent, str) else str(ent.get("name", ent.get("@id", "")))
                if q in name.lower():
                    score += 5

            segments = scene.get("=segments") or scene.get("segments", [])
            for text in [s.get("text", "") if isinstance(s, dict) else str(s) for s in segments]:
                if q in text.lower():
                    score += 1
                    if not context:
                        idx = text.lower().find(q)
                        context = text[max(0, idx - 60): idx + len(q) + 60].strip()

            if score > 0:
                hits.append({
                    "scene_id": sid,
                    "score": score,
                    "where": where,
                    "entity_count": len(entities),
                    "segment_count": len(segments),
                    "context": context[:200],
                })

        hits.sort(key=lambda h: -h["score"])
        return self._send_json(200, {
            "query": query,
            "hits": hits[:limit],
            "count": len(hits),
            "total_scenes": len(self.runtime.vault_scenes),
        })

    def _handle_world_sync(self, body: Dict[str, Any]):
        active_id, vault_root, manifest_path = self._get_active_vault_context()

        if not vault_root or not os.path.isdir(vault_root):
            return self._send_json(400, {"type": "error", "message": "No vault linked or path invalid. Use /vault/link first."})

        if not manifest_path or not os.path.exists(manifest_path):
            manifest_path = os.path.join(vault_root, "vault.manifest.json")

        if not os.path.exists(manifest_path):
            return self._send_json(400, {"type": "error", "error": "manifest_not_found", "path": manifest_path})

        try:
            dry_run = bool(body.get("dry_run", False))
            cfg = parse_manifest_v1(vault_root, manifest_path, default_vault_id=active_id or "unknown", root_dir=ROOT_DIR)

            force = bool(body.get("force", False))
            current_fp = get_vault_fingerprint(vault_root)
            state = get_build_state(vault_root)
            last_fp = state.get("last_vault_fingerprint")
            last_ts = state.get("last_build_ts", 0)
            now = time.time()

            if not force and last_fp == current_fp:
                return self._send_json(200, {
                    "type": "result", "action": "world/sync", "ok": True,
                    "status": "skipped", "reason": "vault_unchanged", "fingerprint": current_fp,
                })

            cooldown = 30
            if not force and (now - last_ts < cooldown):
                wait = int(cooldown - (now - last_ts))
                return self._send_json(429, {
                    "type": "result", "action": "world/sync", "ok": False,
                    "status": "skipped", "reason": "cooldown_active", "retry_after": wait,
                })

            mirror_to_vault = cfg.mirror_to_vault if "mirror_override" not in body else bool(body["mirror_override"])
            make_ro = cfg.make_mirror_readonly if "readonly_override" not in body else bool(body["readonly_override"])

            write_quarantine_marker(vault_root)
            print(f"[VAULT] Sync: Triggering build into {cfg.build_output_dir}")

            ingest_script = os.path.join(ROOT_DIR, "engain_ingest.py")
            _safe_mkdir(cfg.build_output_dir)
            pipeline_dir = os.path.join(ROOT_DIR, "mettaext")

            build_cmd = [sys.executable, ingest_script, "--vault", vault_root, "--out", cfg.build_output_dir, "--pipeline-dir", pipeline_dir]
            build_result: Dict[str, Any] = {"ok": None, "cmd": build_cmd}

            if dry_run:
                build_result.update({"ok": True, "note": "dry_run"})
            else:
                rc, out, err = _run(build_cmd)
                build_result.update({"ok": (rc == 0), "rc": rc, "stdout": out[-500:], "stderr": err[-2000:]})

            cache_files = _count_files(cfg.build_output_dir)
            mirror_result = None
            mirror_root = os.path.join(vault_root, cfg.vault_mirror_dir)

            if mirror_to_vault and (build_result.get("ok") or cache_files > 0):
                mirror_result = rsync_mirror(cfg.build_output_dir, mirror_root, delete=True, dry_run=dry_run)
                if (not dry_run) and make_ro:
                    chmod_readonly(mirror_root)

            load_source = mirror_root if mirror_to_vault else cfg.build_output_dir
            load_results: Dict[str, Any] = {}
            if (not dry_run) and os.path.isdir(load_source):
                load_results = bulk_load_scenes(self.runtime, load_source)

            if cache_files > 0 and not dry_run:
                state["last_vault_fingerprint"] = current_fp
                state["last_build_ts"] = now
                save_build_state(vault_root, state)

            return self._send_json(200, {
                "type": "result", "action": "world/sync",
                "ok": (cache_files > 0),
                "build": {"files": cache_files, "result": build_result},
                "mirror": {"enabled": mirror_to_vault, "mirror_dir": mirror_root, "rsync": mirror_result},
                "load": load_results,
            })
        except Exception as e:
            traceback.print_exc()
            return self._send_json(500, {"type": "error", "message": f"Sync failed: {e}"})

    def _handle_world_load_mirror(self, body: Dict[str, Any]):
        active_id, vault_root, manifest_path = self._get_active_vault_context()
        if not active_id or not vault_root:
            return self._send_json(400, {"type": "error", "message": "No active vault linked."})

        try:
            cfg = parse_manifest_v1(vault_root, manifest_path, default_vault_id=active_id, root_dir=ROOT_DIR)
            load_source = os.path.join(vault_root, cfg.vault_mirror_dir)
            if not os.path.isdir(load_source):
                load_source = cfg.build_output_dir

            results = bulk_load_scenes(self.runtime, load_source)
            return self._send_json(200, {"type": "result", "action": "world/load_mirror", "ok": True, "details": results})
        except Exception as e:
            return self._send_json(500, {"type": "error", "message": str(e)})

    def _handle_transforms(self):
        """
        Lightweight endpoint: returns ONLY entity positions.

        SemanticRenderer polls this at 100ms (10fps) for smooth movement.
        Full /snapshot is too heavy for fast polling.
        """
        runtime = self.runtime
        if not runtime:
            return self._send_json(200, {"transforms": {}, "tick": 0})

        envelope = runtime.get_snapshot()
        payload = envelope.get("payload", envelope) if isinstance(envelope, dict) else {}
        if not isinstance(payload, dict):
            payload = {}

        transforms = {}

        entities = payload.get("entities", {})
        if isinstance(entities, dict):
            for eid, entity in entities.items():
                if not isinstance(entity, dict):
                    continue
                pos = entity.get("pos") or entity.get("position")
                if isinstance(pos, dict):
                    transforms[str(eid)] = {
                        "x": float(pos.get("x", 0)),
                        "y": float(pos.get("y", 0)),
                        "z": float(pos.get("z", 0)),
                    }
                elif isinstance(pos, (list, tuple)) and len(pos) >= 3:
                    transforms[str(eid)] = {
                        "x": float(pos[0]),
                        "y": float(pos[1]),
                        "z": float(pos[2]),
                    }

        bridge = payload.get("bridge_entities", [])
        if isinstance(bridge, list):
            for ent in bridge:
                if not isinstance(ent, dict):
                    continue
                eid = str(ent.get("entity_id") or ent.get("id") or "")
                if not eid or eid in transforms:
                    continue
                t = ent.get("transform", {}).get("position", {})
                if isinstance(t, dict):
                    transforms[eid] = {
                        "x": float(t.get("x", 0)),
                        "y": float(t.get("y", 0)),
                        "z": float(t.get("z", 0)),
                    }

        tick = payload.get("world", {}).get("time", 0)
        return self._send_json(200, {"transforms": transforms, "tick": tick})

    def log_message(self, format, *args):
        pass  # Silence default BaseHTTPRequestHandler logging
