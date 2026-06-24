#!/usr/bin/env python3
"""vault_manager.py - Vault sync, registry, mirroring utilities for EngAIn runtime.

Pure utilities module. No HTTP concerns. No runtime references.
Used by: scene_manager.py, http_handlers.py
"""

import json
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# ── Data Models ──────────────────────────────────────────────────

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


# ── Filesystem Helpers ───────────────────────────────────────────

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


def _run(cmd: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    p = subprocess.run(
        cmd, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
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
                if f.endswith(suffix):
                    count += 1
            else:
                count += 1
    return count


# ── Scene Document Normalization ─────────────────────────────────

def normalize_scene_doc(doc: dict) -> dict:
    """Standardize scene document structure (handles type='scene' slugging)."""
    import re
    if not isinstance(doc, dict):
        return doc

    if doc.get("type") == "scene":
        if "scene_id" not in doc and isinstance(doc.get("id"), str) and doc["id"].strip():
            sid = doc["id"].strip().lower().replace(" ", "_")
            sid = re.sub(r"[^a-zA-Z0-9_]", "", sid)
            doc["scene_id"] = sid

        if "title" not in doc or not isinstance(doc.get("title"), str) or not doc.get("title", "").strip():
            title = None
            segs = doc.get("segments")
            if isinstance(segs, list) and segs:
                s0 = segs[0]
                if isinstance(s0, dict):
                    t = s0.get("text")
                    if isinstance(t, str) and t.strip():
                        title = t.split("\n")[0].strip()[:50]
            doc["title"] = title or doc.get("scene_id") or doc.get("id") or "Untitled Scene"

    return doc


# ── Vault Manifest Validation ────────────────────────────────────

def validate_vault_manifest(m: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(m, dict):
        return False, "manifest_not_object"
    if m.get("spec_version") != "engain.vault_manifest.v1":
        return False, "unsupported_spec_version"
    if not m.get("vault_id"):
        return False, "missing_vault_id"
    content = m.get("content", {})
    if not content:
        return False, "missing_content_section"
    return True, "ok"


# ── Vault Registry ───────────────────────────────────────────────

class VaultRegistry:
    """Persistent registry so the runtime remembers linked vaults across restarts."""

    def __init__(self, registry_path: str):
        self.registry_path = registry_path
        self.state: Dict[str, Any] = {"active_vault_id": None, "vaults": {}}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.registry_path):
            try:
                self.state = _read_json(self.registry_path)
            except Exception:
                self.state = {"active_vault_id": None, "vaults": {}}

    def save(self) -> None:
        _write_json(self.registry_path, self.state)

    def upsert_vault(
        self, vault_id: str, vault_root: str, manifest_path: str, manifest: Dict[str, Any]
    ) -> None:
        self.state.setdefault("vaults", {})
        self.state["vaults"][vault_id] = {
            "vault_root": vault_root,
            "manifest_path": manifest_path,
            "title": manifest.get("title"),
            "spec_version": manifest.get("spec_version"),
            "content": manifest.get("content", {}),
            "ingest": manifest.get("ingest", {}),
            "runtime": manifest.get("runtime", {}),
        }

    def set_active(self, vault_id: str) -> None:
        self.state["active_vault_id"] = vault_id


# ── Manifest Parsing ─────────────────────────────────────────────

def parse_manifest_v1(vault_root: str, manifest_path: str, default_vault_id: str, root_dir: str = "") -> ManifestConfig:
    data = _read_json(manifest_path)
    vault_id = data.get("vault_id") or default_vault_id

    content = data.get("content", {})
    source_md_dir = content.get("source_markdown", {}).get("dir", ".")
    target_zonj_dir = content.get("zonj_scenes", {}).get("dir", "tier3/mettaext/ingested/scenes")

    build = data.get("build", {})
    output_dir = build.get("output_dir")
    if not output_dir:
        output_dir = os.path.join(root_dir, ".vault_cache", vault_id)

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


# ── Sync / Build / Mirror Helpers ────────────────────────────────

def rsync_mirror(src: str, dst: str, delete: bool = True, dry_run: bool = False) -> Dict[str, Any]:
    _safe_mkdir(dst)
    cmd = ["rsync", "-av"]
    if dry_run:
        cmd.append("--dry-run")
    if delete:
        cmd.append("--delete")
    cmd += [src.rstrip("/") + "/", dst.rstrip("/") + "/"]
    rc, out, err = _run(cmd)
    return {"cmd": cmd, "rc": rc, "stdout": out, "stderr": err}


def chmod_readonly(path: str) -> Dict[str, Any]:
    cmd = ["chmod", "-R", "a-w", path]
    rc, out, err = _run(cmd)
    return {"cmd": cmd, "rc": rc, "stdout": out, "stderr": err}


def write_quarantine_marker(vault_root: str) -> None:
    engain_dir = os.path.join(vault_root, ".engain")
    _safe_mkdir(engain_dir)
    marker = os.path.join(engain_dir, "DO_NOT_EDIT.md")
    if not os.path.exists(marker):
        with open(marker, "w", encoding="utf-8") as f:
            f.write(
                "# EngAIn Generated Artifacts (DO NOT EDIT)\n\n"
                "This folder is generated by EngAIn tooling.\n"
                "Edits here will be overwritten on next sync.\n"
            )


def get_vault_fingerprint(vault_root: str) -> str:
    """Compute coarse fingerprint based on max mtime of relevant files."""
    max_mtime = 0.0
    for root, dirs, files in os.walk(vault_root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("mettaext", "godotsim", "EngAIn")]
        for f in files:
            if f.endswith((".md", ".json", ".txt")):
                try:
                    m = os.path.getmtime(os.path.join(root, f))
                    if m > max_mtime:
                        max_mtime = m
                except Exception:
                    pass
    return str(max_mtime)


def get_build_state(vault_root: str) -> Dict[str, Any]:
    path = os.path.join(vault_root, ".engain", "build_state.json")
    if os.path.exists(path):
        try:
            return _read_json(path)
        except Exception:
            pass
    return {}


def save_build_state(vault_root: str, state: Dict[str, Any]) -> None:
    path = os.path.join(vault_root, ".engain", "build_state.json")
    _safe_mkdir(os.path.dirname(path))
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


# ── Bulk Scene Loader ────────────────────────────────────────────

def bulk_load_scenes(runtime, root_dir: str) -> Dict[str, Any]:
    """
    Search and load scenes from a directory into runtime.
    Collision resolution: newest wins. Strict accounting.
    Automatic default scene selection.
    
    runtime must expose: .scenes, .snapshot, .load_scene(), .select_active_scene()
    """
    stats = {
        "attempted": 0,
        "accepted_new": 0,
        "overwritten": 0,
        "rejected": 0,
        "failed": 0,
        "scanned_files": 0,
        "loaded": 0,
        "skipped": 0,
        "skips_by_reason": {
            "not_scene_type": 0,
            "schema_missing_fields": 0,
            "duplicate_scene_id_ignored": 0,
            "duplicate_scene_id_overwritten_pre_load": 0,
        },
        "errors": [],
        "collisions": {},
        "registry_size_before": len(runtime.scenes),
        "registry_size_after": 0,
        "active_scene_before": runtime.snapshot.get("scene_id"),
        "active_scene_after": None,
        "default_scene_selected": False,
        "default_scene_reason": None,
    }

    # Step 1: Collect valid scene candidates
    candidates: Dict[str, Dict[str, Any]] = {}

    for root, _, files in os.walk(root_dir):
        for f in files:
            if not f.endswith(".json"):
                continue
            stats["attempted"] += 1
            stats["scanned_files"] += 1
            fp = os.path.join(root, f)

            try:
                mtime = os.path.getmtime(fp)
                with open(fp, "r", encoding="utf-8") as jf:
                    data = json.load(jf)

                if not isinstance(data, dict):
                    stats["rejected"] += 1
                    stats["skipped"] += 1
                    stats["skips_by_reason"]["not_scene_type"] += 1
                    continue

                if "spec_version" in data or "vault_id" in data or "last_vault_fingerprint" in data:
                    stats["rejected"] += 1
                    stats["skipped"] += 1
                    stats["skips_by_reason"]["not_scene_type"] += 1
                    continue

                data = normalize_scene_doc(data)

                sid = data.get("scene_id") or data.get("@id")
                has_segs = "segments" in data or "=segments" in data

                if not (sid and has_segs):
                    stats["rejected"] += 1
                    stats["skipped"] += 1
                    stats["skips_by_reason"]["schema_missing_fields"] += 1
                    continue

                if sid in candidates:
                    stats["rejected"] += 1
                    stats["skipped"] += 1
                    if sid not in stats["collisions"]:
                        stats["collisions"][sid] = [candidates[sid]["path"]]
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

    # Step 2: Load winners into registry
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

    # Step 3: Default scene selection
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
        first_sid = sorted_sids[0]
        runtime.select_active_scene(first_sid)
        active_after = first_sid
        stats["default_scene_selected"] = True
        stats["default_scene_reason"] = "was_none_selected_first_loaded"
    else:
        active_after = runtime.snapshot.get("scene_id")
        stats["default_scene_selected"] = False
        stats["default_scene_reason"] = "no_suitable_default" if not active_after else "kept_existing_active"

    stats["active_scene_after"] = active_after
    stats["registry_size_after"] = len(runtime.scenes)

    if len(stats["errors"]) > 20:
        stats["errors"] = stats["errors"][:20] + ["...truncated"]

    if stats["collisions"]:
        report = []
        for sid, fps in sorted(stats["collisions"].items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            chosen = candidates[sid]["path"]
            others = [p for p in fps if p != chosen]
            report.append(
                f'scene_id: "{sid}" had {len(fps)} candidates. '
                f"Chosen newest: {chosen}. Overwritten/Ignored: {others}"
            )
        stats["collision_report"] = report

    return stats
