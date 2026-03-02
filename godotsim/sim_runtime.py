#!/usr/bin/env python3
"""sim_runtime.py - EngAIn Runtime - FULL OPERATIONAL WITH SLICE PROTECTION"""

import json
import sys
import os
import time
import copy
import threading
import subprocess
from datetime import datetime

print(f"Current working directory: {os.getcwd()}")
print(f"Script location: {os.path.abspath(__file__)}")

from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from protocol_envelope import ProtocolEnvelope, ProtocolError, create_envelope_for_runtime
import engain_hooks
from vault_linker import VaultLinker
from urllib.parse import parse_qs, urlparse, unquote

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def __hook__(chain, event, module=None, file=None, func=None, **kw):
    """Instrumentation hook for the runtime module."""
    stats = engain_hooks.get_stats()
    
    if event == "call":
        # Hot-path functions: Aggregate in stats
        if func in ("load_scene", "select_active_scene", "validate_vault_manifest", "_read_json", "_normalize_scene_doc"):
            stats[f"{func}_calls"] = stats.get(f"{func}_calls", 0) + 1
            
            # Sampling: record first 3 and then every 50th
            count = stats[f"{func}_calls"]
            if count <= 3 or count % 50 == 0:
                chain.append({
                    "type": "sample",
                    "event": event,
                    "func": func,
                    "module": module,
                    "count": count,
                    "ts": time.time()
                })
            return

        # Control-plane functions: Capture individual checkpoints
        if func in ("_handle_world_sync", "_bulk_load_scenes", "dispatch", "_handle_vault_link"):
             chain.append({
                 "type": "checkpoint",
                 "event": event,
                 "func": func,
                 "module": module,
                 "ts": time.time()
             })
             # Start timer for summary
             stats[f"{func}_start"] = time.time()
             
    elif event == "return":
        # Major control-plane summaries
        if func in ("_handle_world_sync", "_bulk_load_scenes", "dispatch"):
            start = stats.get(f"{func}_start")
            if start:
                ms = (time.time() - start) * 1000
                summary = {
                    "type": "summary",
                    "scope": func,
                    "ms": round(ms, 2)
                }
                # Contextual enrichment
                if func == "_bulk_load_scenes":
                    summary.update({
                        "load_scene_calls": stats.get("load_scene_calls", 0),
                        "select_active_calls": stats.get("select_active_scene_calls", 0),
                        "validate_calls": stats.get("validate_vault_manifest_calls", 0)
                    })
                chain.append(summary)

    elif event == "init":
        chain.append({"type": "module_init", "module": module, "file": file})

# -------------------------
# Vault registry persistence
# -------------------------

def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)

def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_json(path: str, obj: Dict[str, Any]) -> None:
    _ensure_dir(os.path.dirname(path))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

def _norm_abs(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))

def validate_vault_manifest(m: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(m, dict):
        return False, "manifest_not_object"
    if m.get("spec_version") != "engain.vault_manifest.v1":
        return False, "unsupported_spec_version"
    if not m.get("vault_id"):
        return False, "missing_vault_id"
    # New spec: content and build are expected, but relaxed for flexibility
    content = m.get("content", {})
    if not content:
        return False, "missing_content_section"
    return True, "ok"

def _normalize_scene_doc(doc: dict) -> dict:
    if not isinstance(doc, dict):
        return doc

    # Accept "scene v0" schema
    if doc.get("type") == "scene":
        # id contains spaces. want a stable slug for scene_id
        if "scene_id" not in doc and isinstance(doc.get("id"), str) and doc["id"].strip():
            sid = doc["id"].strip().lower().replace(" ", "_")
            import re
            sid = re.sub(r'[^a-zA-Z0-9_]', '', sid)
            doc["scene_id"] = sid

        if "title" not in doc or not isinstance(doc.get("title"), str) or not doc.get("title","").strip():
            title = None
            segs = doc.get("segments")
            if isinstance(segs, list) and segs:
                s0 = segs[0]
                if isinstance(s0, dict):
                    t = s0.get("text")
                    if isinstance(t, str) and t.strip():
                        # Take first line if multiple
                        title = t.split("\n")[0].strip()[:50]
            doc["title"] = title or doc.get("scene_id") or doc.get("id") or "Untitled Scene"

    return doc

@dataclass
class VaultLinkResult:
    ok: bool
    vault_id: Optional[str] = None
    manifest_path: Optional[str] = None
    vault_root: Optional[str] = None
    error: Optional[str] = None

@dataclass
class ManifestConfig:
    vault_id: str
    source_markdown_dir: str
    target_zonj_dir: str
    build_output_dir: str
    mirror_to_vault: bool
    vault_mirror_dir: str
    make_mirror_readonly: bool

class VaultRegistry:
    """
    A small persistent registry so the runtime remembers linked vaults.
    """
    def __init__(self, registry_path: str):
        self.registry_path = registry_path
        self.state: Dict[str, Any] = {"active_vault_id": None, "vaults": {}}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.registry_path):
            try:
                self.state = _read_json(self.registry_path)
            except Exception:
                # If corrupted, keep runtime alive; don't crash on boot.
                self.state = {"active_vault_id": None, "vaults": {}}

    def save(self) -> None:
        _write_json(self.registry_path, self.state)

    def upsert_vault(self, vault_id: str, vault_root: str, manifest_path: str, manifest: Dict[str, Any]) -> None:
        self.state.setdefault("vaults", {})
        self.state["vaults"][vault_id] = {
            "vault_root": vault_root,
            "manifest_path": manifest_path,
            "title": manifest.get("title"),
            "spec_version": manifest.get("spec_version"),
            "content": manifest.get("content", {}),
            "ingest": manifest.get("ingest", {}),
            "runtime": manifest.get("runtime", {})
        }

    def set_active(self, vault_id: str) -> None:
        self.state["active_vault_id"] = vault_id

# Import slice builders - PROTECTION LAYER
try:
    from slice_builders import build_spatial_slice_v1, build_entity_kview_v1, SliceError
    HAS_SLICES = True
    print("✓ Slice builders loaded")
except ImportError as e:
    print(f"Slice builders missing: {e}")
    HAS_SLICES = False

# Import MR kernels
try:
    from spatial3d_mr import step_spatial3d
    from perception_mr import step_perception
    from behavior3d_mr import update_behavior_mr
    HAS_MR = True
except ImportError as e:
    print(f"MR kernels missing: {e}")
    HAS_MR = False

# Import adapters
try:
    from spatial3d_adapter import Spatial3DStateViewAdapter
    from perception_adapter import PerceptionStateView
    from behavior_adapter import BehaviorStateView
    from combat3d_adapter import Combat3DAdapter
    from inventory3d_integration import Inventory3DAdapter
    from dialogue3d_integration import Dialogue3DAdapter
    HAS_ADAPTERS = True
except ImportError as e:
    print(f"Adapters missing: {e}")
    HAS_ADAPTERS = False

print(f"✓ MR kernels | spatial=True, perception=True, behavior=True")

# Kernel contract validation
VALID_KERNEL_RETURN_KEYS = {"deltas", "alerts"}
VALID_OPS = {"set", "add", "remove", "inc", "dec"}

class KernelContractError(RuntimeError):
    pass

# -----------------------------------------------------------------------------
# World Sync Helpers
# -----------------------------------------------------------------------------

def _run(cmd: list[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    p = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return p.returncode, p.stdout, p.stderr

def _safe_mkdir(p: str) -> None:
    os.makedirs(p, exist_ok=True)

def _count_files(root: str, suffix: Optional[str] = None) -> int:
    path_root = os.path.abspath(root)
    if not os.path.exists(path_root):
        return 0
    count = 0
    for r, d, files in os.walk(path_root):
        for f in files:
            if suffix:
                if f.endswith(suffix): count += 1
            else:
                count += 1
    return count

def _write_quarantine_marker(vault_root: str) -> None:
    engain_dir = os.path.join(vault_root, ".engain")
    _safe_mkdir(engain_dir)
    marker = os.path.join(engain_dir, "DO_NOT_EDIT.md")
    if not os.path.exists(marker):
        with open(marker, "w", encoding="utf-8") as f:
            f.write("# EngAIn Generated Artifacts (DO NOT EDIT)\n\n"
                    "This folder is generated by EngAIn tooling.\n"
                    "Edits here will be overwritten on next sync.\n")

def _parse_manifest_v1(vault_root: str, manifest_path: str, default_vault_id: str) -> ManifestConfig:
    data = _read_json(manifest_path)
    vault_id = data.get("vault_id") or default_vault_id

    content = data.get("content", {})
    source_md_dir = content.get("source_markdown", {}).get("dir", ".")
    target_zonj_dir = content.get("zonj_scenes", {}).get("dir", "mettaext/ingested/scenes")

    build = data.get("build", {})
    output_dir = build.get("output_dir")
    if not output_dir:
        output_dir = os.path.join(ROOT_DIR, ".vault_cache", vault_id)

    runtime = data.get("runtime", {})
    mirror_to_vault = bool(runtime.get("mirror_to_vault", False))
    vault_mirror_dir = runtime.get("vault_mirror_dir", f".engain/build/{vault_id}")
    make_mirror_readonly = bool(runtime.get("make_mirror_readonly", True))

    return ManifestConfig(
        vault_id=vault_id,
        source_markdown_dir=source_md_dir,
        target_zonj_dir=target_zonj_dir,
        build_output_dir=output_dir,
        mirror_to_vault=mirror_to_vault,
        vault_mirror_dir=vault_mirror_dir,
        make_mirror_readonly=make_mirror_readonly,
    )

def _rsync_mirror(src: str, dst: str, delete: bool = True, dry_run: bool = False) -> Dict[str, Any]:
    _safe_mkdir(dst)
    cmd = ["rsync", "-av"]
    if dry_run: cmd.append("--dry-run")
    if delete: cmd.append("--delete")
    cmd += [src.rstrip("/") + "/", dst.rstrip("/") + "/"]

    rc, out, err = _run(cmd)
    return {"cmd": cmd, "rc": rc, "stdout": out, "stderr": err}

def _get_vault_fingerprint(vault_root: str) -> str:
    """Compute a coarse fingerprint based on max mtime of relevant files."""
    max_mtime = 0.0
    for root, dirs, files in os.walk(vault_root):
        # Skip hidden/infrastructure dirs
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("mettaext", "godotsim", "EngAIn")]
        for f in files:
            if f.endswith((".md", ".json", ".txt")):
                try:
                    m = os.path.getmtime(os.path.join(root, f))
                    if m > max_mtime: max_mtime = m
                except: pass
    return str(max_mtime)

def _get_build_state(vault_root: str) -> Dict[str, Any]:
    path = os.path.join(vault_root, ".engain", "build_state.json")
    if os.path.exists(path):
        try: return _read_json(path)
        except: pass
    return {}

def _save_build_state(vault_root: str, state: Dict[str, Any]) -> None:
    path = os.path.join(vault_root, ".engain", "build_state.json")
    _safe_mkdir(os.path.dirname(path))
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except: pass

def _bulk_load_scenes(runtime: Any, root_dir: str) -> Dict[str, Any]:
    """
    Search and load scenes from a directory. 
    Implements collision resolution (newest wins), strict registry accounting,
    and automatic default scene selection.
    """
    stats = {
        "attempted": 0,       # Total JSON files touched
        "accepted_new": 0,    # Unique scene IDs added to registry
        "overwritten": 0,     # Scene IDs that replaced existing registry entries
        "rejected": 0,        # Files skipped (not a scene, missing fields, or older duplicate)
        "failed": 0,          # Files that crashed (JSON error, etc)
        "scanned_files": 0,   # (Legacy) same as attempted
        "loaded": 0,          # (Legacy) sum of accepted_new + overwritten
        "skipped": 0,         # (Legacy) same as rejected
        "skips_by_reason": {
            "not_scene_type": 0,
            "schema_missing_fields": 0,
            "duplicate_scene_id_ignored": 0,
            "duplicate_scene_id_overwritten_pre_load": 0
        },
        "errors": [],
        "collisions": {}, # scene_id -> [list of files]
        "registry_size_before": len(runtime.scenes),
        "registry_size_after": 0,
        "active_scene_before": runtime.snapshot.get("scene_id"),
        "active_scene_after": None,
        "default_scene_selected": False,
        "default_scene_reason": None
    }

    # Step 1: Collect all valid scene candidates
    candidates: Dict[str, Dict[str, Any]] = {} # scene_id -> {path, mtime, data}

    for root, _, files in os.walk(root_dir):
        for f in files:
            if not f.endswith(".json"): continue
            stats["attempted"] += 1
            stats["scanned_files"] += 1
            fp = os.path.join(root, f)
            
            try:
                mtime = os.path.getmtime(fp)
                with open(fp, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                
                # Filter: must be a dict
                if not isinstance(data, dict):
                    stats["rejected"] += 1
                    stats["skipped"] += 1
                    stats["skips_by_reason"]["not_scene_type"] += 1
                    continue

                # Filter: Skip manifest-like objects or build states
                if "spec_version" in data or "vault_id" in data or "last_vault_fingerprint" in data:
                    stats["rejected"] += 1
                    stats["skipped"] += 1
                    stats["skips_by_reason"]["not_scene_type"] += 1
                    continue

                # Normalization (handles type="scene" and stable slugging)
                data = _normalize_scene_doc(data)
                
                # Validation
                sid = data.get("scene_id") or data.get("@id")
                has_segs = "segments" in data or "=segments" in data
                
                if not (sid and has_segs):
                    stats["rejected"] += 1
                    stats["skipped"] += 1
                    stats["skips_by_reason"]["schema_missing_fields"] += 1
                    continue

                # Collision Check (Newest wins in current scan)
                if sid in candidates:
                    stats["rejected"] += 1
                    stats["skipped"] += 1
                    if sid not in stats["collisions"]: stats["collisions"][sid] = [candidates[sid]["path"]]
                    stats["collisions"][sid].append(fp)
                    
                    if mtime > candidates[sid]["mtime"]:
                        stats["skips_by_reason"]["duplicate_scene_id_overwritten_pre_load"] += 1
                        candidates[sid] = {"path": fp, "mtime": mtime, "data": data}
                    else:
                        stats["skips_by_reason"]["duplicate_scene_id_ignored"] += 1
                else:
                    candidates[sid] = {"path": fp, "mtime": mtime, "data": data}

            except json.JSONDecodeError:
                stats["failed"] += 1
                stats["errors"].append(f"{f}: JSON parse error")
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"{f}: {str(e)}")

    # Step 2: Load the winners into registry (without activating yet)
    sorted_sids = sorted(candidates.keys())
    for sid in sorted_sids:
        info = candidates[sid]
        try:
            load_status = runtime.load_scene(info["data"], activate=False)
            if load_status == "accepted_new":
                stats["accepted_new"] += 1
            else:
                stats["overwritten"] += 1
            stats["loaded"] += 1
        except Exception as e:
            stats["failed"] += 1
            stats["errors"].append(f"Load failed for {sid} ({info['path']}): {str(e)}")

    # Step 3: Default Scene Selection Logic
    active_before = stats["active_scene_before"]
    active_after = active_before
    
    if active_before and active_before in runtime.scenes:
        runtime.select_active_scene(active_before)
        active_after = active_before
        stats["default_scene_selected"] = True
        stats["default_scene_reason"] = "kept_existing"
    elif "start" in runtime.scenes:
        runtime.select_active_scene("start")
        active_after = "start"
        stats["default_scene_selected"] = True
        stats["default_scene_reason"] = "used_start_scene"
    elif not active_before and sorted_sids:
        # Pick the first one alphabetically
        first_sid = sorted_sids[0]
        runtime.select_active_scene(first_sid)
        active_after = first_sid
        stats["default_scene_selected"] = True
        stats["default_scene_reason"] = "was_none_selected_first_loaded"
    else:
        # No change or no scenes found
        active_after = runtime.snapshot.get("scene_id")
        stats["default_scene_selected"] = False
        stats["default_scene_reason"] = "no_suitable_default" if not active_after else "kept_existing_active"

    stats["active_scene_after"] = active_after
    stats["registry_size_after"] = len(runtime.scenes)

    # Truncate errors if too many
    if len(stats["errors"]) > 20:
        stats["errors"] = stats["errors"][:20] + ["...truncated"]
    
    # Format collision report for top offenders
    if stats["collisions"]:
        report = []
        for sid, fps in sorted(stats["collisions"].items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            chosen = candidates[sid]["path"]
            others = [p for p in fps if p != chosen]
            report.append(f"scene_id: \"{sid}\" had {len(fps)} candidates. Chosen newest: {chosen}. Overwritten/Ignored: {others}")
        stats["collision_report"] = report

    return stats

def _chmod_readonly(path: str) -> Dict[str, Any]:
    cmd = ["chmod", "-R", "a-w", path]
    rc, out, err = _run(cmd)
    return {"cmd": cmd, "rc": rc, "stdout": out, "stderr": err}

class SafeJSONEncoder(json.JSONEncoder):
    """Handles sets, tuples, and non-serializable objects gracefully."""
    def default(self, obj):
        if isinstance(obj, (set, tuple)):
            return list(obj)
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

def deep_freeze(obj):
    """Debug-only: catches mutation attempts if you use immutable containers later"""
    if isinstance(obj, dict):
        return {k: deep_freeze(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_freeze(v) for v in obj]
    return obj

def stable_hash(obj) -> str:
    """Deterministic hash of state for debugging"""
    import hashlib
    payload = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()

class EngAInRuntime:
    def __init__(self):
        self.snapshot = {
            "scene_id": None,
            "entities": {},
            "spatial": {},
            "perception": {},
            "behavior": {},
            "world": {"time": 0.0, "weather": "clear"},
            "events": [],
            "scene": None,
            "scene_raw": None
        }
        self.vault_linker = VaultLinker()
        self.vault_scenes = {}
        self.scenes = {} # scene_id -> scene_doc
        self._last_result = None  # inline result buffer for /command
        
        self.delta_queue = []
        self.command_queue = []
        
        self.envelope = create_envelope_for_runtime()
        print(f"  ✓ Protocol: {self.envelope.PROTOCOL_NAME} v{self.envelope.version}")
        print(f"  ✓ Epoch: {self.envelope.epoch_id}")
        
        self._init_subsystems()
        self._init_combat()
        self._init_inventory()
        self._init_dialogue()

        # Vault management setup
        self.vault_registry = VaultRegistry(os.path.join(ROOT_DIR, "vault_registry.json"))
        active_id = self.vault_registry.state.get("active_vault_id")
        if active_id and active_id in self.vault_registry.state.get("vaults", {}):
            v = self.vault_registry.state["vaults"][active_id]
            self.snapshot["active_vault_id"] = active_id
            self.snapshot["vaults"] = {active_id: v}
        
        self.rng = 42  # Deterministic seed for reproducibility
        self.debug = False  # Set True for deep_freeze checks
        
        self.running = True
        self.sim_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.sim_thread.start()
        
        print("  → son of a bitch.... its finally fixed.. whats next boys?.  ")
        print("EngAIn Runtime: Initialized")
    
    def _init_subsystems(self):
        if HAS_ADAPTERS:
            try:
                self.spatial = Spatial3DStateViewAdapter()
                print("  ✓ Spatial3D")
            except:
                self.spatial = None
            
            try:
                self.perception = PerceptionStateView({})
                print("  ✓ Perception")
            except:
                self.perception = None
            
            try:
                self.behavior = BehaviorStateView({"entities": {}})
                print("  ✓ Behavior")
            except:
                self.behavior = None
        else:
            self.spatial = None
            self.perception = None
            self.behavior = None

    def _init_combat(self):
        """Initialize Combat3D subsystem"""
        try:
            self.combat = Combat3DAdapter()
            print("  ✓ Combat3D")
            
            # Register test entities (remove in production)
            self.combat.register_entity("player", health=100, max_health=100)
            self.combat.register_entity("guard", health=100, max_health=100)
            self.combat.register_entity("enemy", health=50, max_health=50)
        except Exception as e:
            print(f"  ✗ Combat3D failed: {e}")
            self.combat = None

    def _init_inventory(self):
        """Initialize Inventory3D subsystem"""
        try:
            self.inventory = Inventory3DAdapter()
            print("  ✓ Inventory3D")
            
            # Register test entities
            self.inventory.register_entity("player", load_allowed=100)
            self.inventory.register_entity("guard", load_allowed=80)
            
            # Register test items
            self.inventory.register_item("sword", size=10, wearable=True, location="world")
            self.inventory.register_item("shield", size=15, wearable=True, location="world")
            self.inventory.register_item("potion", size=2, takeable=True, location="world")
            self.inventory.register_item("armor", size=20, wearable=True, location="world")
            
            # Items for fumble test
            self.inventory.register_item("potion1", size=2, location="world")
            self.inventory.register_item("potion2", size=2, location="world")
            self.inventory.register_item("potion3", size=2, location="world")
            self.inventory.register_item("potion4", size=2, location="world")
            self.inventory.register_item("potion5", size=2, location="world")
            self.inventory.register_item("potion6", size=2, location="world")
            self.inventory.register_item("potion7", size=2, location="world")
            self.inventory.register_item("potion8", size=2, location="world")
        except Exception as e:
            print(f"  ✗ Inventory3D failed: {e}")
            self.inventory = None

    def _init_dialogue(self):
        """Initialize Dialogue3D subsystem"""
        try:
            self.dialogue = Dialogue3DAdapter()
            print("  ✓ Dialogue3D")
            
            self.dialogue.register_entity("player", knowledge_flags=[])
            self.dialogue.register_entity("guard", knowledge_flags=["fire_crystal_location"])
            self.dialogue.register_entity("merchant", knowledge_flags=["sword_upgrade"])
        except Exception as e:
            print(f"  ✗ Dialogue3D failed: {e}")
            self.dialogue = None
    
    def _create_entity_state(self, entity_id: str, entity_type: str, 
                            position: Tuple[float, float, float], **kwargs) -> Dict[str, Any]:
        return {
            "id": entity_id,
            "type": entity_type,
            "position": position,  # Canonical key
            "velocity": (0.0, 0.0, 0.0),  # Canonical key
            "health": kwargs.get("health", 100),
            "max_health": kwargs.get("max_health", 100),
            "ai_enabled": kwargs.get("ai_enabled", False),
            **kwargs
        }
    
    def _simulation_loop(self):
        dt = 0.016
        while self.running:
            start_time = time.time()
            self._process_commands()
            self._update_subsystems(dt)
            self.snapshot["world"]["time"] += dt
            elapsed = time.time() - start_time
            sleep_time = max(0, dt - elapsed)
            time.sleep(sleep_time)
    
    def _process_commands(self):
        while self.command_queue:
            cmd = self.command_queue.pop(0)
            self._execute_command(cmd)
    
    def _execute_command(self, cmd: Dict[str, Any]):
        action = cmd.get("action")
        
        if action == "spawn_entity":
            entity_id = cmd.get("entity_id")
            entity_type = cmd.get("entity_type")
            position = cmd.get("position", {"x": 0, "y": 0, "z": 0})
            properties = cmd.get("properties", {})
            
            pos_tuple = (position.get("x", 0), position.get("y", 0), position.get("z", 0))
            
            entity_state = self._create_entity_state(
                entity_id, entity_type, pos_tuple,
                ai_enabled=properties.get("ai_enabled", False),
                **properties
            )
            
            self.snapshot["entities"][entity_id] = entity_state
            
            if self.spatial:
                try:
                    self.spatial.spawn_entity(entity_id, pos_tuple)
                    print(f"✓ Spawned {entity_type} '{entity_id}' (Spatial3D)")
                except:
                    print(f"✓ Spawned {entity_type} '{entity_id}'")
            else:
                print(f"✓ Spawned {entity_type} '{entity_id}'")

        elif action == "update_entity":
            entity = cmd.get("entity")
            state = cmd.get("state", {})
            
            if entity and entity in self.snapshot["entities"]:
                # Normalize Godot types to Python tuples
                if "position" in state:
                    p = state["position"]
                    if isinstance(p, dict):
                        self.snapshot["entities"][entity]["pos"] = (
                            float(p.get("x", 0)), 
                            float(p.get("y", 0)), 
                            float(p.get("z", 0))
                        )
                
                if "velocity" in state:
                    v = state["velocity"]
                    if isinstance(v, dict):
                        self.snapshot["entities"][entity]["vel"] = (
                            float(v.get("x", 0)), 
                            float(v.get("y", 0)), 
                            float(v.get("z", 0))
                        )
                
                # Update other fields
                for k, v in state.items():
                    if k not in ["position", "velocity", "rotation"]:
                        self.snapshot["entities"][entity][k] = v
            elif entity and entity not in self.snapshot["entities"]:
                # Auto-create if missing (lazy spawn for player)
                print(f"Lazy spawning {entity} from update")
                p = state.get("position", {"x":0,"y":0,"z":0})
                pos_tuple = (p.get("x", 0), p.get("y", 0), p.get("z", 0))
                
                # Filter out position from state to prevent dual-argument error
                create_kwargs = {k:v for k,v in state.items() if k != "position"}
                
                self.snapshot["entities"][entity] = self._create_entity_state(
                    entity, "player", pos_tuple, **create_kwargs
                )
        
        elif action == "interact":
            self._handle_interaction(cmd)
        
        elif action == "reload_blocks":
            print("Reloading blocks...")
        
        elif action == "dump_state":
            self._dump_full_state()

        # ── Text commands (from Godot boot / CLI) ────────────────
        text = cmd.get("text", "").strip().lower()
        if text and not action:
            result = self.handle_text_command(text)
            self._last_result = result
    
    def _handle_interaction(self, cmd: Dict[str, Any]):
        entity = cmd.get("entity", "unknown")
        player_rep = cmd.get("player_rep", 50)
        player_gold = cmd.get("player_gold", 0)
        context = cmd.get("context", "default")
        
        print(f"\n[INTERACTION] {entity} (context: {context})")
        
        if entity == "greeter":
            greeter_id = "greeter_main"
            pos_tuple = (5.0, 0.0, 3.0)
            
            # Simple dialogue lookup
            if player_rep < 30:
                dialogue = "What do you want?"
                mood = "unfriendly"
            elif player_rep < 70:
                dialogue = "Hello there."
                mood = "neutral"
            else:
                dialogue = "Welcome back, friend!"
                mood = "friendly"
            
            entity_state = self._create_entity_state(
                greeter_id, "greeter", pos_tuple,
                dialogue=dialogue, mood=mood,
                reputation=player_rep, ai_enabled=True
            )
            
            self.snapshot["entities"][greeter_id] = entity_state
            
            if self.spatial:
                try:
                    self.spatial.spawn_entity(greeter_id, pos_tuple)
                except:
                    pass
            
            # Register with behavior
            if self.behavior:
                try:
                    self.behavior.add_behavior_entity(
                        greeter_id,
                        initial_state="idle",
                        patrol_points=[(5,0,3), (10,0,5), (5,0,3)]
                    )
                    print(f"  [BEHAVIOR] AI enabled for {greeter_id}")
                    
                    # Seed perception so greeter can react
                    if greeter_id not in self.snapshot["perception"]:
                        self.snapshot["perception"][greeter_id] = {}
                    
                    if player_rep < 30:
                        # Unfriendly - watching player closely
                        self.snapshot["perception"][greeter_id] = {
                            "visible_entities": ["player"],
                            "focus_target": "player"
                        }
                        print(f"  [PERCEPTION] Greeter hostile - focused on player")
                    else:
                        # Friendly - aware but not focused
                        self.snapshot["perception"][greeter_id] = {
                            "visible_entities": ["player"],
                            "focus_target": None
                        }
                        print(f"  [PERCEPTION] Greeter friendly - player visible")
                    
                except:
                    pass
            
            self.snapshot["events"].append({
                "type": "dialogue_started",
                "npc_id": greeter_id,
                "dialogue": dialogue,
                "mood": mood
            })
            
            print(f"  Greeter spawned: '{dialogue}' (mood: {mood})")
        
        elif entity == "merchant":
            merchant_id = "merchant_main"
            pos_tuple = (8.0, 0.0, 5.0)
            
            if player_gold < 100:
                dialogue = "Come back when you have more coin."
                willing_to_trade = False
            else:
                dialogue = "What would you like to buy?"
                willing_to_trade = True
            
            entity_state = self._create_entity_state(
                merchant_id, "merchant", pos_tuple,
                dialogue=dialogue,
                willing_to_trade=willing_to_trade,
                gold_required=100,
                inventory=["sword", "potion", "shield"]
            )
            
            self.snapshot["entities"][merchant_id] = entity_state
            
            if self.spatial:
                try:
                    self.spatial.spawn_entity(merchant_id, pos_tuple)
                except:
                    pass
            
            self.snapshot["events"].append({
                "type": "trade_initiated",
                "merchant_id": merchant_id,
                "willing": willing_to_trade,
                "gold": player_gold
            })
            
            print(f"  Merchant spawned: '{dialogue}'")
            print(f"  Inventory: {entity_state['inventory']}")
    
    def _update_subsystems(self, dt: float):
        """Sealed snapshot → run all kernels → apply once"""
        tick = self.snapshot["world"]["time"]
        pre_hash = stable_hash(self.snapshot)
        snapshot_pack = self.build_snapshot_pack()
        
        all_deltas = []
        all_alerts = []
        
        # Run kernels in fixed order (seal → run → collect)
        # Note: Using tick() for now until adapters support step() interface
        
        # Combat3D
        if self.combat:
            try:
                for delta_type, payload in self.combat.tick(dt):
                    all_deltas.append((delta_type, payload))
            except Exception as e:
                print(f"[COMBAT ERROR] {e}")
        
        # Inventory3D
        if self.inventory:
            try:
                inv_deltas, inv_alerts = self.inventory.tick(dt)
                all_alerts.extend(inv_alerts)
            except Exception as e:
                print(f"[INVENTORY ERROR] {e}")
        
        # Dialogue3D
        if self.dialogue:
            try:
                dlg_deltas, dlg_alerts = self.dialogue.tick(dt)
                all_alerts.extend(dlg_alerts)
            except Exception as e:
                print(f"[DIALOGUE ERROR] {e}")
        
        # Spatial3D (entity-based, runs with slice protection)
        entity_ids = list(self.snapshot["entities"].keys())
        if entity_ids and HAS_MR and self.spatial and HAS_SLICES:
            try:
                spatial_state = {"entities": {}}
                for eid in entity_ids:
                    try:
                        slice_view = build_entity_kview_v1(self.snapshot, eid)
                        spatial_state["entities"][eid] = {
                            "pos": slice_view.pos,
                            "vel": slice_view.vel
                        }
                    except SliceError as e:
                        print(f"[SLICE ERROR] {eid}: {e}")
                        continue
                
                snapshot_in = {"spatial3d": spatial_state}
                snapshot_out, accepted, alerts = step_spatial3d(snapshot_in, [], dt)
                
                updated_spatial = snapshot_out.get("spatial3d", {})
                for eid, spatial_data in updated_spatial.get("entities", {}).items():
                    if eid in self.snapshot["entities"]:
                        self.snapshot["entities"][eid]["position"] = list(spatial_data["pos"])
                        self.snapshot["entities"][eid]["velocity"] = list(spatial_data["vel"])
            except Exception as e:
                print(f"[SPATIAL ERROR] {e}")
        
        # Perception (entity-based)
        if self.perception and entity_ids:
            try:
                self.perception.set_spatial_state(self.snapshot)
                perception_deltas, perception_alerts = self.perception.perception_step(
                    current_tick=int(tick)
                )
                for delta in perception_deltas:
                    self._apply_delta(delta)
            except Exception as e:
                print(f"[PERCEPTION ERROR] {e}")
        
        # Behavior (entity-based)
        if self.behavior and entity_ids:
            try:
                self.behavior.set_spatial_state(self.snapshot)
                self.behavior.set_perception_state(self.snapshot.get("perception", {}))
                behavior_deltas, behavior_alerts = self.behavior.behavior_step(
                    current_tick=tick,
                    delta_time=dt
                )
                if behavior_deltas:
                    print(f"[BEHAVIOR] {len(behavior_deltas)} deltas fired")
                for delta in behavior_deltas:
                    self._apply_delta(delta)
            except Exception as e:
                print(f"[BEHAVIOR ERROR] {e}")
        
        # Apply all collected deltas and alerts
        self._apply_deltas(all_deltas)
        self._push_alerts(all_alerts)
        
        post_hash = stable_hash(self.snapshot)
        if self.debug:
            print(f"[TICK {tick}] state hash: {pre_hash[:12]} → {post_hash[:12]}")

    def _apply_deltas(self, deltas: list):
        """Apply collected deltas to committed state"""
        for delta in deltas:
            # Standard delta application
            domain = delta.get("domain")
            op = delta.get("op")
            path = delta.get("path")
            value = delta.get("value")
            
            # For now, just log - actual application depends on op type
            print(f"  [DELTA] {domain}/{op}: {path}")

    def _push_alerts(self, alerts: list):
        """Push collected alerts to handlers"""
        for alert in alerts:
            alert_type = alert.get("type", "")
            
            # Route to appropriate handler based on source domain
            if "inventory" in alert_type or alert_type in ["item_taken", "item_dropped", "item_worn"]:
                self._apply_inventory_alert(alert)
            elif "combat" in alert_type or alert_type in ["entity_died", "attack_hit", "attack_miss"]:
                self._apply_combat_alert(alert)
            elif "dialogue" in alert_type or alert_type in ["dialogue_started", "knowledge_shared"]:
                self._apply_dialogue_alert(alert)
            else:
                print(f"  [ALERT] {alert_type}: {alert}")

    def _apply_inventory_alert(self, alert: Dict[str, Any]):
        """Process inventory alerts"""
        alert_type = alert.get("type")
        
        if alert_type == "item_taken":
            actor = alert.get("actor")
            item = alert.get("item")
            print(f"  📦 {actor} picked up {item}")
        
        elif alert_type == "item_dropped":
            actor = alert.get("actor")
            item = alert.get("item")
            location = alert.get("location")
            print(f"  📦 {actor} dropped {item} at {location}")
        
        elif alert_type == "item_worn":
            actor = alert.get("actor")
            item = alert.get("item")
            print(f"  👕 {actor} equipped {item}")
        
        elif alert_type == "item_removed":
            actor = alert.get("actor")
            item = alert.get("item")
            print(f"  👕 {actor} unequipped {item}")
        
        elif alert_type == "take_failed":
            reason = alert.get("reason")
            actor = alert.get("actor")
            item = alert.get("item")
            
            if reason == "too_heavy":
                current = alert.get("current_weight")
                item_weight = alert.get("item_weight")
                limit = alert.get("limit")
                print(f"  ⚠️  {actor} can't carry {item}: too heavy ({current}+{item_weight} > {limit})")
            elif reason == "too_many_items":
                count = alert.get("carry_count")
                limit = alert.get("limit")
                print(f"  ⚠️  {actor} fumbling: too many items ({count}/{limit})")
            else:
                print(f"  ⚠️  {actor} can't take {item}: {reason}")
        
        elif alert_type == "overloaded":
            entity = alert.get("entity")
            weight = alert.get("current_weight")
            limit = alert.get("limit")
            print(f"  ⚠️  {entity} overloaded: {weight}/{limit}")
        
        elif alert_type == "fumble_risk":
            entity = alert.get("entity")
            count = alert.get("carry_count")
            limit = alert.get("limit")
            print(f"  ⚠️  {entity} fumble risk: {count}/{limit} items")

    def _apply_dialogue_alert(self, alert: Dict[str, Any]):
        """Process dialogue alerts"""
        alert_type = alert.get("type")
        
        if alert_type == "dialogue_started":
            speaker = alert.get("speaker")
            listener = alert.get("listener")
            print(f"  💬 {speaker} speaks to {listener}")
        
        elif alert_type == "knowledge_shared":
            asker = alert.get("asker")
            topic = alert.get("topic")
            print(f"  📚 {asker} learned: {topic}")
        
        elif alert_type == "knowledge_unknown":
            topic = alert.get("topic")
            print(f"  ❓ Topic unknown: {topic}")
        
        elif alert_type == "branch_selected":
            speaker = alert.get("speaker")
            branch_id = alert.get("branch_id")
            print(f"  🔀 {speaker} chose: {branch_id}")

    def _apply_combat_alert(self, alert: Dict[str, Any]):
        """Process combat alerts"""
        alert_type = alert.get("type")
        
        if alert_type == "entity_died":
            entity_id = alert.get("entity_id")
            print(f"  💀 {entity_id} has died")
            
            # Update main snapshot
            if entity_id in self.snapshot["entities"]:
                self.snapshot["entities"][entity_id]["alive"] = False
                self.snapshot["entities"][entity_id]["state"] = "dead"
            
            # Disable navigation
            if self.behavior:
                self.behavior.set_behavior_state(entity_id, "dead")
        
        elif alert_type == "low_health_warning":
            entity_id = alert.get("entity_id")
            health = alert.get("health")
            print(f"  ⚠️  {entity_id} low health: {health}")
            
            # Set low_health flag for behavior
            if self.behavior:
                # Trigger flee behavior
                pass
        
        elif alert_type == "wound_state_change":
            entity_id = alert.get("entity_id")
            old_state = alert.get("old_state")
            new_state = alert.get("new_state")
            print(f"  🩹 {entity_id}: {old_state} → {new_state}")
        
        elif alert_type == "damage_applied":
            target = alert.get("target")
            amount = alert.get("amount")
            source = alert.get("source")
            print(f"  ⚔️  {source} hits {target} for {amount} damage")

        elif alert_type == "attack_hit":
            attacker = alert.get("attacker")
            target = alert.get("target")
            damage = alert.get("damage")
            print(f"  ⚔️  {attacker} hits {target} for {damage} damage")
        
        elif alert_type == "attack_miss":
            attacker = alert.get("attacker")
            target = alert.get("target")
            print(f"  ⭕ {attacker} misses {target}")

    def _apply_delta(self, delta):
        delta_type = delta.type
        payload = delta.payload
        
        print(f"  🔥 [{delta_type}]")
        
        if delta_type == "navigation3d/request_path":
            entity_id = payload.get("entity_id")
            if entity_id:
                print(f"     Path request for {entity_id}")
        
        elif delta_type == "behavior3d/attack":
            attacker = payload.get("attacker")
            target = payload.get("target")
            print(f"     {attacker} → attacks → {target}")
            
            self.snapshot["events"].append({
                "type": "attack_initiated",
                "attacker": attacker,
                "target": target
            })
        
        elif delta_type == "behavior3d/high_intent":
            entity_id = payload.get("entity_id")
            intent = payload.get("intent", 0.0)
            print(f"     {entity_id} HIGH INTENT: {intent:.2f}")
    
    def _dump_full_state(self):
        print("\n=== STATE DUMP ===")
        print(json.dumps(self.snapshot, indent=2, default=str))
        
        if self.behavior:
            print("\n=== BEHAVIOR STATES ===")
            for entity_id in self.snapshot["entities"].keys():
                behavior_state = self.behavior.get_behavior_state(entity_id)
                if behavior_state:
                    print(f"{entity_id}:")
                    print(f"  intent={behavior_state.get('intent', 0):.2f}")
                    print(f"  alertness={behavior_state.get('alertness', 0):.2f}")
                    print(f"  threat={behavior_state.get('threat', 0):.2f}")
    
    def handle_text_command(self, text: str) -> Dict[str, Any]:
        """Process natural-language commands: look, examine, status, etc."""
        scene = self.snapshot.get("scene")

        if text in ("look", "l"):
            if not scene:
                return {"type": "result", "command": text,
                        "text": "You see nothing. No scene is loaded."}


            sid = scene.get("scene_id", "unknown")
            where = scene.get("where") or "an unknown place"
            when_val = scene.get("when") or "an unknown time"
            entities = scene.get("entities", [])
            segments = scene.get("segments", [])

            # Build description from first few segments
            desc_lines = []
            for seg in segments[:5]:
                if isinstance(seg, dict):
                    line = seg.get("text") or seg.get("narration") or seg.get("dialogue") or ""
                    if isinstance(line, str) and line.strip():
                        desc_lines.append(line.strip())
                elif isinstance(seg, str) and seg.strip():
                    desc_lines.append(seg.strip())

            description = " ".join(desc_lines) if desc_lines else "The scene stretches before you."

            # Entity summary
            entity_names = []
            for e in entities[:10]:
                if isinstance(e, dict):
                    name = e.get("name") or e.get("@id") or e.get("id") or "?"
                    entity_names.append(str(name))
                elif isinstance(e, str):
                    entity_names.append(e)

            return {
                "type": "result",
                "command": text,
                "scene_id": sid,
                "where": where,
                "when": when_val,
                "text": description,
                "entities_present": entity_names,
                "total_segments": len(segments),
            }

        elif text.startswith("examine ") or text.startswith("x "):
            target = text.split(" ", 1)[1].strip()
            if not scene:
                return {"type": "result", "command": text,
                        "text": "Nothing to examine. No scene loaded."}

            entities = scene.get("entities", [])
            for e in entities:
                if isinstance(e, dict):
                    eid = str(e.get("name") or e.get("@id") or e.get("id") or "")
                    if target.lower() in eid.lower():
                        return {"type": "result", "command": text,
                                "text": f"You examine {eid}.",
                                "entity": e}

            return {"type": "result", "command": text,
                    "text": f"You don't see '{target}' here."}

        elif text in ("status", "stat"):
            entity_count = len(self.snapshot.get("entities", {}))
            world = self.snapshot.get("world", {})
            scene_id = (scene.get("scene_id") or scene.get("@id") or "none") if scene else "none"
            return {
                "type": "result", "command": text,
                "scene_id": scene_id,
                "entities_active": entity_count,
                "world_time": world.get("time", 0.0),
                "weather": world.get("weather", "unknown"),
            }

        elif text in ("segments", "seg"):
            if not scene:
                return {"type": "result", "command": text, "text": "No scene loaded."}
            segs = scene.get("segments", [])
            return {
                "type": "result", "command": text,
                "total": len(segs),
                "preview": [str(s)[:120] for s in segs[:10]],
            }

        else:
            return {"type": "result", "command": text,
                    "text": f"Unknown command: '{text}'",
                    "hint": "Try: look, examine <entity>, status, segments"}

    def load_scene(self, scene_doc: Dict[str, Any], activate: bool = False) -> str:
        """
        Parse scene data and store in registry. 
        Returns status: "accepted_new" | "overwritten"
        """
        scene_id = scene_doc.get("@id") or scene_doc.get("scene_id") or "unknown"
        
        # Build normalized view
        norm = {
            "scene_id": scene_id,
            "where": scene_doc.get("@where") or scene_doc.get("where"),
            "when": scene_doc.get("@when") or scene_doc.get("when"),
            "entities": scene_doc.get("@entities") or scene_doc.get("entities", []),
            "segments": scene_doc.get("=segments") or scene_doc.get("segments", []),
        }

        if isinstance(norm["entities"], dict):
            norm["entities"] = list(norm["entities"].values())
        if norm["entities"] is None: norm["entities"] = []
        if norm["segments"] is None: norm["segments"] = []

        status = "overwritten" if scene_id in self.scenes else "accepted_new"

        # Registry Persistence
        self.scenes[scene_id] = {
            "raw": scene_doc,
            "norm": norm
        }

        if activate:
            self.select_active_scene(scene_id)

        return status

    
    def _extract_entities_for_scene(self):
        """Run SceneExtractor on the active scene, populate entity_cards."""
        if _scene_extractor is None:
            return
        if not self.snapshot.get("scene"):
            return
        scene_doc = self.snapshot["scene"]
        try:
            self.entity_cards = _scene_extractor.extract(scene_doc)
            names = [c.name for c in self.entity_cards.values()]
            print(f"[EXTRACT] {len(self.entity_cards)} entities: {names}")
        except Exception as e:
            print(f"[EXTRACT] Error: {e}")
            self.entity_cards = {}

    def select_active_scene(self, scene_id: str) -> bool:
            """Activates a scene from the registry into the current snapshot."""
            if scene_id not in self.scenes:
                return False
                
            info = self.scenes[scene_id]
            self.snapshot["scene_raw"] = info["raw"]
            self.snapshot["scene"] = info["norm"]
            self.snapshot["scene_id"] = scene_id
            
            # Sync entities
            entities_dict = {}
            for ent in info["norm"]["entities"]:
                if isinstance(ent, dict):
                    eid = ent.get("@id") or ent.get("id") or str(ent.get("name"))
                    if eid:
                        entities_dict[eid] = ent
            
            if entities_dict:
                self.snapshot["entities"] = entities_dict
                
            return True

    def add_command(self, cmd: Dict[str, Any]):
        self.command_queue.append(cmd)
    
    def build_snapshot_pack(self):
        """Build snapshot pack for kernel invocation"""
        state = copy.deepcopy(self.snapshot)
        
        # Passthrough slices for subsystems
        pack = {
            "inventory3d": state.get("inventory3d", {}),
            "combat3d": state.get("combat3d", {}),
            "dialogue3d": state.get("dialogue3d", {}),
        }
        
        if getattr(self, "debug", False):
            pack = deep_freeze(pack)
        
        return pack
    
    def _run_kernel(self, domain, kernel_fn, intent, snapshot_pack, rng, tick):
        """Run a kernel with strict contract enforcement"""
        own_state = copy.deepcopy(self.snapshot.get(domain, {}))

        result = kernel_fn(
            intent=intent,
            own_state=own_state,
            foreign=snapshot_pack,
            rng_seed=rng,
            now_tick=tick,
        )

        if not isinstance(result, dict):
            raise KernelContractError(f"{domain} returned non-dict: {type(result)}")

        extra = set(result.keys()) - VALID_KERNEL_RETURN_KEYS
        if extra:
            raise KernelContractError(f"{domain} returned illegal fields: {sorted(extra)}")

        deltas = result.get("deltas", [])
        alerts = result.get("alerts", [])

        if not isinstance(deltas, list):
            raise KernelContractError(f"{domain} deltas must be list, got {type(deltas)}")
        if not isinstance(alerts, list):
            raise KernelContractError(f"{domain} alerts must be list, got {type(alerts)}")

        for d in deltas:
            if not isinstance(d, dict):
                raise KernelContractError(f"{domain} delta must be dict: {d}")

            if d.get("domain") != domain:
                raise KernelContractError(f"Cross-domain delta blocked from {domain}: {d}")

            if d.get("op") not in VALID_OPS:
                raise KernelContractError(f"Invalid op in {domain}: {d}")

            if not isinstance(d.get("path"), str):
                raise KernelContractError(f"Invalid path in {domain}: {d}")

        return deltas, alerts
    
    def get_snapshot(self) -> Dict[str, Any]:
        """Get current snapshot wrapped in protocol envelope"""
        snapshot = copy.deepcopy(self.snapshot)
        
        # Clear ephemeral events AFTER copy
        self.snapshot["events"] = []

        # Wrap in protocol envelope with hash
        tick = snapshot["world"]["time"]
        # Wrap in protocol envelope with hash
        tick = snapshot["world"]["time"]
        
        if self.combat:
            try:
                snapshot["combat"] = self.combat.get_all_state()
            except AttributeError:
                snapshot["combat"] = {}
        
        if self.inventory:
            try:
                snapshot["inventory"] = self.inventory.get_all_state()
            except AttributeError:
                snapshot["inventory"] = {}
        
        if self.dialogue:
            try:
                snapshot["dialogue"] = self.dialogue.get_all_state()
            except AttributeError:
                snapshot["dialogue"] = {}
            
        return self.envelope.wrap_snapshot(snapshot, tick)
    
    def shutdown(self):
        self.running = False
        self.sim_thread.join()

class CommandDispatcher:
    def __init__(self, runtime):
        self.runtime = runtime

    def dispatch(self, raw_input: Any) -> Dict[str, Any]:
        """
        Normalize and route commands from HTTP or internal sources.
        """
        # Verbose logging for debugging
        print(f"\n[DISPATCH] Input type: {type(raw_input)}")
        
        if isinstance(raw_input, str):
            print(f"[DISPATCH] String command: '{raw_input}'")
            return self.runtime.handle_text_command(raw_input)
            
        if not isinstance(raw_input, dict):
            return {"type": "error", "message": f"Invalid request format: {type(raw_input)}"}

        # Normalize command/action keys
        command = (raw_input.get("command") or raw_input.get("action") or "").strip().lower()
        text = (raw_input.get("text") or "").strip().lower()
        
        # Effective command string prioritizing command > text
        # But if command is generic "command" or "action", ignore it in favor of text
        if command in ("command", "action", ""):
            cmd_str = text or command
        else:
            cmd_str = command

        print(f"[DISPATCH] Normalized command string: '{cmd_str}' (from cmd='{command}', text='{text}')")

        # 1. Gameplay Dispatch
        # (Reserved for future complex multi-action routing)

        # 2. Direct Adapter Calls (Immediate)
        if cmd_str in ("damage", "combat/damage"):
            if not self.runtime.combat: return {"type": "error", "status": "combat_not_loaded"}
            self.runtime.combat.handle_delta("combat3d/apply_damage", {
                "source": raw_input.get("source", "unknown"),
                "target": raw_input.get("target"),
                "amount": raw_input.get("damage", 25)
            })
            return {"type": "ack", "status": "damage_applied"}

        if cmd_str in ("take", "inventory/take"):
            if not self.runtime.inventory: return {"type": "error", "status": "inventory_not_loaded"}
            self.runtime.inventory.handle_delta("inventory3d/take", {
                "actor": raw_input.get("actor"),
                "item": raw_input.get("item")
            })
            return {"type": "ack", "status": "take_queued"}

        if cmd_str in ("drop", "inventory/drop"):
            if not self.runtime.inventory: return {"type": "error", "status": "inventory_not_loaded"}
            self.runtime.inventory.handle_delta("inventory3d/drop", {
                "actor": raw_input.get("actor"),
                "item": raw_input.get("item"),
                "location": raw_input.get("location", "world")
            })
            return {"type": "ack", "status": "drop_queued"}

        if cmd_str in ("wear", "inventory/wear"):
            if not self.runtime.inventory: return {"type": "error", "status": "inventory_not_loaded"}
            self.runtime.inventory.handle_delta("inventory3d/wear", {
                "actor": raw_input.get("actor"),
                "item": raw_input.get("item")
            })
            return {"type": "ack", "status": "wear_queued"}

        if cmd_str in ("say", "dialogue/say"):
            if not self.runtime.dialogue: return {"type": "error", "status": "dialogue_not_loaded"}
            self.runtime.dialogue.handle_delta("dialogue3d/say", raw_input)
            return {"type": "ack", "status": "say_queued"}

        if cmd_str in ("ask", "dialogue/ask"):
            if not self.runtime.dialogue: return {"type": "error", "status": "dialogue_not_loaded"}
            self.runtime.dialogue.handle_delta("dialogue3d/ask", raw_input)
            return {"type": "ack", "status": "ask_queued"}

        # 3. Simulation Mutations (Queued)
        if cmd_str in ("spawn_entity", "update_entity", "interact", "reload_blocks", "dump_state"):
            self.runtime.add_command(raw_input)
            return {"type": "ack", "status": "queued", "command": cmd_str}

        # 4. Text Pipeline (look, examine, status, etc)
        if cmd_str:
            print(f"[DISPATCH] Routing '{cmd_str}' to text pipeline")
            return self.runtime.handle_text_command(cmd_str)

        return {"type": "error", "message": f"Unknown command: {cmd_str}"}


class RuntimeHTTPHandler(BaseHTTPRequestHandler):
    runtime: EngAInRuntime = None

    def _send_json(self, status_code: int, data: Dict[str, Any]):
        try:
            response_json = json.dumps(data, cls=SafeJSONEncoder)
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(response_json))
            self.end_headers()
            self.wfile.write(response_json.encode('utf-8'))
        except Exception as e:
            print(f"Serialization Error: {e}")
            self.send_error(500, f"Serialization Error: {e}")


    def _handle_vault_link(self, body: Dict[str, Any]):
        vault_path = body.get("vault_path")
        manifest_path = body.get("manifest_path")
        manifest_relpath = body.get("manifest_relpath", "vault.manifest.json")
        set_active = bool(body.get("set_active", True))

        if not manifest_path and not vault_path:
            self._send_json(400, {"type": "error", "error": "missing_vault_path_or_manifest_path"})
            return

        if manifest_path:
            mp = _norm_abs(manifest_path)
            vr = _norm_abs(os.path.dirname(mp))
        else:
            vr = _norm_abs(vault_path)
            mp = _norm_abs(os.path.join(vr, manifest_relpath))

        if not os.path.exists(mp):
            self._send_json(404, {"type": "error", "error": "manifest_not_found", "manifest_path": mp})
            return

        try:
            manifest = _read_json(mp)
        except Exception as e:
            self._send_json(400, {"type": "error", "error": "manifest_parse_failed", "detail": str(e)})
            return

        ok, reason = validate_vault_manifest(manifest)
        if not ok:
            self._send_json(400, {"type": "error", "error": "manifest_invalid", "reason": reason})
            return

        vault_id = manifest["vault_id"]

        # Persist registry
        self.runtime.vault_registry.upsert_vault(vault_id=vault_id, vault_root=vr, manifest_path=mp, manifest=manifest)
        if set_active:
            self.runtime.vault_registry.set_active(vault_id)
        self.runtime.vault_registry.save()

        # Reflect into runtime snapshot
        self.runtime.snapshot.setdefault("vaults", {})
        self.runtime.snapshot["vaults"][vault_id] = {
            "vault_root": vr,
            "manifest_path": mp,
            "title": manifest.get("title"),
        }
        if set_active:
            self.runtime.snapshot["active_vault_id"] = vault_id

        self._send_json(200, {
            "type": "result",
            "action": "vault/link",
            "ok": True,
            "vault_id": vault_id,
            "vault_root": vr,
            "manifest_path": mp,
            "active_vault_id": self.runtime.snapshot.get("active_vault_id")
        })

    def do_GET(self):
        """Healthcheck and metadata discovery."""
        parsed_path = self.path.split('?')
        base_path = parsed_path[0].rstrip('/')
        query_str = parsed_path[1] if len(parsed_path) > 1 else ""
        
        # Simple param parser with unquote support
        params = {}
        if query_str:
            for pair in query_str.split('&'):
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    params[unquote(k)] = unquote(v)

        # after you build params from query string
        q = params.get("q", "")
        limit_str = params.get("limit", "20")
        mode = params.get("mode", "all")

        try:
            limit = int(limit_str)
        except Exception:
            limit = 20

        if not q:
            return self._send_json(400, {"error": "missing ?q= parameter"})

        return self._handle_vault_search(q, limit, mode)

        if base_path in ("", "/health", "/status"):
            data = {
                "ok": True,
                "service": "engain",
                "ts": int(time.time()),
                "pid": os.getpid()
            }
            if params.get("debug") == "1":
                roots = [ROOT_DIR]
                runtime = engain_hooks.HookRuntime(roots, enable_profiling=True)
                def _probe(): return data
                _, chain = runtime.run(_probe)
                data.setdefault("debug", {})["chain"] = chain
            return self._send_json(200, data)

        elif base_path == "/snapshot":
            envelope = self.runtime.get_snapshot()
            return self._send_json(200, envelope)

        elif base_path == "/vault/status":
            status = self.runtime.vault_linker.get_status()
            status["vault_scenes_registered"] = len(getattr(self.runtime, "vault_scenes", {}))
            return self._send_json(200, status)

        elif base_path == "/vault/search":
            q = params.get("q", "")
            limit_str = params.get("limit", "20")
            try:
                limit = int(limit_str)
            except Exception:
                limit = 20
            
            if not q:
                return self._send_json(400, {"error": "missing ?q= parameter"})
            return self._handle_vault_search(q, limit)

        self._send_json(404, {"type": "error", "error": "not_found", "path": self.path})

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body_raw = self.rfile.read(content_length)
        
        print(f"\n[HTTP POST] {self.path} ({content_length} bytes)")
        
        try:
            if not body_raw:
                self._send_json(400, {"type": "error", "error": "empty_body"})
                return



            body = json.loads(body_raw.decode('utf-8'))
            
            # Wrap execution with Instrumentation
            roots = [ROOT_DIR]
            runtime = engain_hooks.HookRuntime(roots, enable_profiling=True)
            
            # We wrap the main dispatch logic
            def _dispatch_and_respond():
                # --- HARD ROUTING ---
                
                if self.path == "/world/sync":
                    return self._handle_world_sync(body)
                
                if self.path == "/command":
                    return self._handle_command(body)
                
                if self.path == "/scene/load":
                    return self._handle_scene_load(body)
                
                elif self.path == "/vault/link":
                    manifest = body.get("manifest")
                    vault_root = body.get("vault_root")
                    if not manifest or not vault_root:
                        self._send_json(400, {"status":"error","error":"need manifest + vault_root"})
                        return
                    result = self.runtime.vault_linker.link(manifest, vault_root)
                    if result.get("status") == "ok":
                        loaded = 0
                        for sid, scene in self.runtime.vault_linker.get_all_scenes().items():
                            self.runtime.vault_scenes[sid] = scene
                            loaded += 1
                        result["scenes_registered"] = loaded
                    self._send_json(200, result)
                    return
                
                if self.path == "/world/load_mirror":
                    return self._handle_world_load_mirror(body)
                
                # Legacy support: if path matches a known legacy endpoint, route it
                if self.path in ("/combat/damage", "/inventory/take", "/inventory/drop", "/inventory/wear"):
                    if isinstance(body, dict):
                        body["command"] = self.path.lstrip("/")
                    return self._handle_command(body)

                # Fallback
                return self._send_json(404, {"type": "error", "error": "not_found", "path": self.path})

            # Run with instrumentation and capture result or error
            # We need to catch send_json within the hook or return the data?
            # Our send_json sends response immediately. This is fine.
            # But we want to attach the chain.
            # I'll modify _send_json or intercept the response.
            
            # Intercept _send_json by temporarily wrapping it
            orig_send_json = self._send_json
            
            def _wrapped_send_json(code, data):
                if isinstance(data, dict):
                    data.setdefault("debug", {})
                    # Retrieve the chain list directly from context
                    data["debug"]["chain"] = engain_hooks.get_chain()
                return orig_send_json(code, data)
            
            self._send_json = _wrapped_send_json
            
            try:
                runtime.run(_dispatch_and_respond)
            finally:
                 self._send_json = orig_send_json
            
        except json.JSONDecodeError as e:
            self._send_json(400, {"type": "error", "error": "invalid_json", "detail": str(e)})
        except Exception as e:
            print(f"[HTTP POST] Server Error: {e}")
            import traceback

# ── Scene Extractor (interactive entity system) ──────────────────
try:
    from scene_extractor import SceneExtractor
    _scene_extractor = SceneExtractor()
    print("[BOOT] SceneExtractor loaded")
except ImportError:
    _scene_extractor = None
    print("[BOOT] SceneExtractor not found — interactive commands disabled")
    traceback.print_exc()
    self._send_json(500, {"type": "error", "error": "internal_error", "detail": str(e)})

    def _handle_command(self, body: Dict[str, Any]):
        # No fallback to self.path. Use payload fields only.
        if not isinstance(body, dict):
             return self._send_json(400, {"type": "error", "error": "body_not_object"})

        text = body.get("text") or body.get("command") or body.get("action")
        
        if not text or not isinstance(text, str):
            return self._send_json(400, {
                "type": "error", 
                "error": "missing_command_text",
                "hint": "POST /command with JSON: {\"text\":\"look\"}"
            })

        dispatcher = CommandDispatcher(self.runtime)
        result = dispatcher.dispatch(body)
        self._send_json(200, result)

    def _handle_world_sync(self, body: Dict[str, Any]):
        # Prefer active vault from registry
        vault_root = None
        active_id = self.runtime.snapshot.get("active_vault_id")
        manifest_path = None

        if active_id and "vaults" in self.runtime.snapshot and active_id in self.runtime.snapshot["vaults"]:
            v = self.runtime.snapshot["vaults"][active_id]
            vault_root = v.get("vault_root")
            manifest_path = v.get("manifest_path")
        
        # Fallback to simple link if manifest.md exists (legacy support)
        if not vault_root:
            legacy_manifest = os.path.join(ROOT_DIR, "vault.manifest.md")
            if os.path.exists(legacy_manifest):
                try:
                    with open(legacy_manifest, "r") as f:
                        for line in f:
                            if "Active Vault Source" in line:
                                vault_root = line.split("`")[1]
                                break
                except: pass

        if not vault_root or not os.path.isdir(vault_root):
            return self._send_json(400, {"type": "error", "message": "No vault linked or path invalid. Use /vault/link first."})

        # Manifest resolution
        if not manifest_path or not os.path.exists(manifest_path):
            manifest_path = os.path.join(vault_root, "vault.manifest.json")
        
        if not os.path.exists(manifest_path):
            return self._send_json(400, {"type": "error", "error": "manifest_not_found", "path": manifest_path})

        try:
            dry_run = bool(body.get("dry_run", False))
            cfg = _parse_manifest_v1(vault_root, manifest_path, default_vault_id=active_id or "unknown")
            
            # --- GUARDS ---
            force = bool(body.get("force", False))
            current_fp = _get_vault_fingerprint(vault_root)
            state = _get_build_state(vault_root)
            
            last_fp = state.get("last_vault_fingerprint")
            last_ts = state.get("last_build_ts", 0)
            now = time.time()
            
            # Change guard
            if not force and last_fp == current_fp:
                print(f"[VAULT] Sync skipped: Vault unchanged ({current_fp})")
                return self._send_json(200, {
                    "type": "result", "action": "world/sync", "ok": True, 
                    "status": "skipped", "reason": "vault_unchanged", "fingerprint": current_fp
                })
            
            # Cooldown guard (30s)
            cooldown = 30
            if not force and (now - last_ts < cooldown):
                wait = int(cooldown - (now - last_ts))
                print(f"[VAULT] Sync skipped: Cooldown active ({wait}s left)")
                return self._send_json(429, {
                    "type": "result", "action": "world/sync", "ok": False,
                    "status": "skipped", "reason": "cooldown_active", "retry_after": wait
                })

            # Optional overrides
            mirror_to_vault = cfg.mirror_to_vault if "mirror_override" not in body else bool(body["mirror_override"])
            make_ro = cfg.make_mirror_readonly if "readonly_override" not in body else bool(body["readonly_override"])

            # Quarantine Marker
            _write_quarantine_marker(vault_root)

            # Build Step (The actual Ingest)
            print(f"[VAULT] Triggering build into: {cfg.build_output_dir}")
            ingest_script = os.path.join(ROOT_DIR, "engain_ingest.py")
            _safe_mkdir(cfg.build_output_dir)
            
            pipeline_dir = os.path.join(ROOT_DIR, "mettaext")
            build_cmd = [
                sys.executable, ingest_script,
                "--vault", vault_root,
                "--out", cfg.build_output_dir,
                "--pipeline-dir", pipeline_dir,
            ]
            
            build_result = {
                "ok": None,
                "cmd": build_cmd,
                "ingest_script": ingest_script,
                "python": sys.executable,
                "vault_root": vault_root,
            }
            
            if dry_run:
                build_result.update({"ok": True, "note": "dry_run enabled; build skipped"})
            else:
                rc, out, err = _run(build_cmd)
                build_result.update({"ok": (rc == 0), "rc": rc, "stdout": out[-500:], "stderr": err[-2000:]})

            # Mirror Step
            mirror_result = None
            chmod_result = None
            mirror_root = os.path.join(vault_root, cfg.vault_mirror_dir)

            # Count cache once before deciding to mirror
            cache_files = _count_files(cfg.build_output_dir)

            # Mirror if build succeeded OR build produced any files (partial success)
            mirror_ok_to_run = bool(build_result.get("ok")) or (cache_files > 0)

            if mirror_to_vault and mirror_ok_to_run:
                mirror_result = _rsync_mirror(
                    cfg.build_output_dir,
                    mirror_root,
                    delete=True,
                    dry_run=dry_run,
                )
                if (not dry_run) and make_ro:
                    chmod_result = _chmod_readonly(mirror_root)

            # Stats (re-count mirror after rsync; cache_files already computed)
            mirror_files = _count_files(mirror_root) if mirror_to_vault else 0

            # --- INTERNAL LOAD STEP (B1) ---
            # Automatically load scenes from the mirror (or cache if mirror disabled)
            load_source = mirror_root if mirror_to_vault else cfg.build_output_dir
            load_results = {
                "attempted": 0, "accepted_new": 0, "overwritten": 0, "rejected": 0,
                "loaded": 0, "failed": 0, "errors": [],
                "registry_size_after": len(self.runtime.scenes),
                "active_scene_before": self.runtime.snapshot.get("scene_id"),
                "active_scene_after": self.runtime.snapshot.get("scene_id"),
                "default_scene_selected": False,
                "default_scene_reason": "load_skipped"
            }
            
            if (not dry_run) and os.path.isdir(load_source):
                load_results = _bulk_load_scenes(self.runtime, load_source)

            # Consider the sync "ok" if we have usable output (cache has files)
            overall_ok = (cache_files > 0)
            
            # Persistence: Update Build State
            if overall_ok and not dry_run:
                state["last_vault_fingerprint"] = current_fp
                state["last_build_ts"] = now
                _save_build_state(vault_root, state)

            return self._send_json(200, {
                "type": "result",
                "action": "world/sync",
                "ok": overall_ok,
                "vault_id": cfg.vault_id,
                "build": {
                    "output_dir": cfg.build_output_dir,
                    "files": cache_files,
                    "result": build_result,
                },
                "mirror": {
                    "enabled": mirror_to_vault,
                    "mirror_dir": mirror_root,
                    "files": mirror_files,
                    "rsync": mirror_result,
                    "ccmd_readonly": chmod_result
                },
                "load": load_results
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._send_json(500, {"type": "error", "message": f"Sync failed: {e}"})

    def _handle_world_load_mirror(self, body: Dict[str, Any]):
        """Internal load from current active vault's mirror."""
        active_id = self.runtime.snapshot.get("active_vault_id")
        if not active_id or "vaults" not in self.runtime.snapshot or active_id not in self.runtime.snapshot["vaults"]:
             return self._send_json(400, {"type": "error", "message": "No active vault linked."})
        
        v = self.runtime.snapshot["vaults"][active_id]
        vault_root = v.get("vault_root")
        manifest_path = v.get("manifest_path")
        
        try:
            cfg = _parse_manifest_v1(vault_root, manifest_path, default_vault_id=active_id)
            load_source = os.path.join(vault_root, cfg.vault_mirror_dir)
            
            if not os.path.isdir(load_source):
                load_source = cfg.build_output_dir

            results = {
                "attempted": 0, "accepted_new": 0, "overwritten": 0, "rejected": 0,
                "loaded": 0, "failed": 0, "errors": [],
                "registry_size_after": len(self.runtime.scenes),
                "active_scene_before": self.runtime.snapshot.get("scene_id"),
                "active_scene_after": self.runtime.snapshot.get("scene_id"),
                "default_scene_selected": False,
                "default_scene_reason": "load_skipped"
            }
            if os.path.isdir(load_source):
                results = _bulk_load_scenes(self.runtime, load_source)
            
            return self._send_json(200, {"type": "result", "action": "world/load_mirror", "ok": True, "details": results})
        except Exception as e:
            return self._send_json(500, {"type": "error", "message": str(e)})


    def _handle_vault_search(self, query: str, limit: int = 20, mode: str = "all"):
        """Search across all linked vault scenes."""
        if not hasattr(self.runtime, "vault_scenes") or not self.runtime.vault_scenes:
            return self._send_json(200, {
                "query": query, "hits": [], "count": 0,
                "error": "no vault linked"
            })

        q = query.lower()
        hits = []

        for sid, scene in self.runtime.vault_scenes.items():
            where = scene.get("where", "") or ""

            # Runtime-side filter: only some folders when mode == "playable"
            if mode == "playable":
                # Example: keep only main book content, adjust to your folders
                if not (
                    where.startswith("Book 1") or
                    where.startswith("Book 2") or
                    where.startswith("Book 3")
                ):
                    continue

            score = 0
            matched_segments = []
            context = ""

            # Search scene_id
            if q in sid.lower():
                score += 10

            # Search entities
            entities = scene.get("@entities") or scene.get("entities", [])
            if isinstance(entities, list):
                for ent in entities:
                    name = ent if isinstance(ent, str) else str(ent.get("name", ent.get("@id", "")))
                    if q in name.lower():
                        score += 5

            # Search tags
            tags = scene.get("@tags", [])
            for tag in tags:
                if q in str(tag).lower():
                    score += 3

            # Search segments text
            segments = scene.get("=segments") or scene.get("segments", [])
            for i, seg in enumerate(segments):
                text = ""
                if isinstance(seg, dict):
                    text = seg.get("text", "") or seg.get("narration", "") or seg.get("dialogue", "")
                elif isinstance(seg, str):
                    text = seg
                if q in text.lower():
                    score += 1
                    matched_segments.append(i)
                    if not context:
                        # Grab a snippet around the match
                        idx = text.lower().find(q)
                        start = max(0, idx - 60)
                        end = min(len(text), idx + len(q) + 60)
                        context = text[start:end].strip()

            if score > 0:
                hits.append({
                    "scene_id": sid,
                    "score": score,
                    "where": scene.get("@where", ""),
                    "chapter": scene.get("@chapter"),
                    "entity_count": len(entities) if isinstance(entities, list) else 0,
                    "segment_count": len(segments),
                    "matched_segments": matched_segments[:5],
                    "context": context[:200] if context else "",
                })

        # Sort by score descending
        hits.sort(key=lambda h: -h["score"])
        hits = hits[:limit]

        return self._send_json(200, {
            "query": query,
            "hits": hits,
            "count": len(hits),
            "total_scenes": len(self.runtime.vault_scenes)
        })

    def _handle_scene_load(self, body: Dict[str, Any]):
        if not isinstance(body, dict):
             return self._send_json(400, {"type": "error", "error": "body_not_object"})

        # Extract ZONJ document
        doc = body.get("zonj") or body.get("scene")
        if not doc:
            # If not wrapped, use the whole input safely
            doc = {k: v for k, v in body.items() if k not in ("command", "action")}
        
        # Vault fallback: if we only have an ID or partial doc, try to find in registered vault_scenes
        has_segments = "segments" in doc or "=segments" in doc
        if not has_segments and hasattr(self.runtime, "vault_scenes"):
            req_id = doc.get("scene_id") or doc.get("@id") or body.get("scene_id")
            if req_id in self.runtime.vault_scenes:
                doc = self.runtime.vault_scenes[req_id]

        doc = _normalize_scene_doc(doc)

        # Validator: accept either (scene_id and segments) OR (type=="scene" and id and segments)
        # Note: id is moved to scene_id by normalizer for type=="scene".
        has_id = doc.get("scene_id") or doc.get("@id") or (doc.get("type") == "scene" and doc.get("id"))
        has_segments = "segments" in doc or "=segments" in doc
        
        if not (has_id and has_segments):
             print(f"[HTTP] ERROR: Invalid ZONJ doc sent to /scene/load")
             return self._send_json(400, {
                 "type": "error", 
                 "error": "invalid_zonj", 
                 "message": "Missing required fields: scene_id (or id) and segments"
             })
            
        self.runtime.load_scene(doc, activate=True)
        scene_id = doc.get("@id") or doc.get("scene_id") or "unknown"
        return self._send_json(200, {"type": "result", "action": "scene/load", "scene_id": scene_id, "status": "loaded"})
    
    def log_message(self, format, *args):
        pass

def main():
    print("=" * 50)
    print("EngAIn Runtime Server")
    print("=" * 50)
    
    runtime = EngAInRuntime()
    RuntimeHTTPHandler.runtime = runtime
    server = ThreadingHTTPServer(('localhost', 8080), RuntimeHTTPHandler)
    
    print("\nServer running on http://localhost:8080 (MT)")
    print("Press Ctrl+C to stop\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        runtime.shutdown()
        server.shutdown()
        print("Goodbye!")


if __name__ == "__main__":
    main()


    def handle_entities(self, args):
        """List all interactive entities in the current scene."""
        if not hasattr(self, 'entity_cards') or not self.entity_cards:
            return {"text": "No entities extracted for this scene. Load a scene first.", "entities": []}

        lines = []
        entities_list = []
        for key, card in sorted(self.entity_cards.items(), key=lambda x: -x[1].extracted["mention_count"]):
            c = card.to_dict()
            mood_str = c["mood"]
            type_str = c["type"] or "?"
            role_str = c["role"] or "?"
            marker = " *" if c["has_override"] else ""
            lines.append(f"  [{c['name']}] {type_str}/{role_str} — mood: {mood_str}{marker}")
            entities_list.append(c)

        header = f"=== Entities in scene ({len(self.entity_cards)}) ==="
        footer = "\n  (* = has override)"
        return {
            "text": header + "\n" + "\n".join(lines) + footer,
            "entities": entities_list,
        }

    def handle_examine(self, args):
        """Examine an entity: show description, type, mood, knowledge."""
        if not args:
            return {"text": "Examine what? Try: examine <name>"}
        target = " ".join(args).lower().strip()

        if not hasattr(self, 'entity_cards') or not self.entity_cards:
            return {"text": "No entities in this scene."}

        # Fuzzy match
        card = self._find_entity(target)
        if not card:
            return {"text": f"You don't see '{target}' here."}

        c = card.to_dict()
        desc = card.get_description()
        knowledge = ", ".join(c["knowledge"]) if c["knowledge"] else "unknown"

        lines = [
            f"=== {c['name']} ===",
            f"  Type: {c['type'] or 'unknown'}",
            f"  Role: {c['role'] or 'unknown'}",
            f"  Mood: {c['mood']}",
            f"  Knowledge: {knowledge}",
            f"  Mentions: {c['mention_count']}",
            f"",
            f"  {desc}",
        ]

        if c["has_override"]:
            lines.append(f"\n  [has designer override]")

        return {
            "text": "\n".join(lines),
            "entity": c,
            "description": desc,
        }

    def handle_talk(self, args):
        """Talk to an entity: show dialogue (override first, then extracted)."""
        if not args:
            return {"text": "Talk to whom? Try: talk to <name>"}

        # Strip leading "to" if present
        if args[0].lower() == "to" and len(args) > 1:
            args = args[1:]
        target = " ".join(args).lower().strip()

        if not hasattr(self, 'entity_cards') or not self.entity_cards:
            return {"text": "No entities in this scene."}

        card = self._find_entity(target)
        if not card:
            return {"text": f"You don't see '{target}' here."}

        dialogue = card.get_dialogue()
        mood = card.get_mood()

        if not dialogue:
            # No dialogue — but entity exists. Show a slot.
            return {
                "text": f"{card.name} is here, but has no dialogue yet.\n"
                        f"  Mood: {mood}\n"
                        f"  Knowledge: {', '.join(card.extracted['knowledge']) or 'unknown'}\n"
                        f"  [dialogue slot — ready for authoring]",
                "entity": card.to_dict(),
                "dialogue": [],
                "has_slot": True,
            }

        lines = [f"=== {card.name} ({mood}) ===", ""]
        for d in dialogue:
            source = d.get("source", "extracted")
            marker = "[override] " if source == "override" else ""
            lines.append(f'  {marker}"{d["line"]}"')

        return {
            "text": "\n".join(lines),
            "entity": card.to_dict(),
            "dialogue": dialogue,
        }

    def handle_mood(self, args):
        """Show or describe an entity's mood."""
        if not args:
            return {"text": "Whose mood? Try: mood <name>"}
        target = " ".join(args).lower().strip()

        if not hasattr(self, 'entity_cards') or not self.entity_cards:
            return {"text": "No entities in this scene."}

        card = self._find_entity(target)
        if not card:
            return {"text": f"You don't see '{target}' here."}

        mood = card.get_mood()
        all_moods = card.extracted["moods"]
        override_mood = card.override.get("mood")

        lines = [f"=== {card.name} — Mood ==="]
        lines.append(f"  Current: {mood}")
        if override_mood:
            lines.append(f"  (set by override)")
        if all_moods:
            lines.append(f"  Detected across text: {', '.join(set(all_moods))}")

        return {"text": "\n".join(lines), "mood": mood}

    def handle_override(self, args):
        """Set an override on an entity. Usage: override <name> <field> <value>"""
        if len(args) < 3:
            return {"text": "Usage: override <name> <field> <value>\n"
                            "  Fields: type, role, mood, description\n"
                            "  Example: override torhh mood protective"}

        target = args[0].lower()
        field = args[1].lower()
        value = " ".join(args[2:])

        if not hasattr(self, 'entity_cards') or not self.entity_cards:
            return {"text": "No entities in this scene."}

        card = self._find_entity(target)
        if not card:
            return {"text": f"Entity '{target}' not found."}

        if field not in ("type", "role", "mood", "description"):
            return {"text": f"Unknown field '{field}'. Use: type, role, mood, description"}

        card.override[field] = value

        # Save to disk
        scene_id = self.snapshot.get("scene", {}).get("@id") or self.snapshot.get("scene", {}).get("scene_id", "unknown")
        _scene_extractor.save_overrides(scene_id, self.entity_cards)

        return {
            "text": f"Override set: {card.name}.{field} = {value}\n  (saved to disk)",
            "entity": card.to_dict(),
        }

    def _find_entity(self, target):
        """Fuzzy-find entity by name (case-insensitive, partial match)."""
        if not hasattr(self, 'entity_cards'):
            return None
        # Exact match
        if target in self.entity_cards:
            return self.entity_cards[target]
        # Partial match
        for key, card in self.entity_cards.items():
            if target in key or key in target:
                return card
        return None

